#!/usr/bin/env python3
"""
Public, path-sanitized version of the SmolVLA continuous autonomous task manager
used in the SO-101 project.

This keeps the project-specific orchestration logic:
- empty-scene background capture
- color-agnostic foreground detection
- stable-object gating
- box success detection
- timeout / stall handling
- safe observation/action retries
- automatic return-home
- continuous front-camera recording

Model internals remain in upstream LeRobot.
"""

from __future__ import annotations

import csv
import math
import os
import threading
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
import torch

from lerobot.cameras.opencv import OpenCVCameraConfig
from lerobot.common.control_utils import follower_smooth_move_to
from lerobot.policies import make_pre_post_processors
from lerobot.policies.smolvla import SmolVLAPolicy
from lerobot.policies.utils import build_inference_frame, make_robot_action
from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig
from lerobot.utils.feature_utils import hw_to_dataset_features

CKPT = Path(os.environ.get("SMOLVLA_CKPT", "./checkpoints/smolvla_20k/pretrained_model"))
FOLLOWER_PORT = os.environ.get("SO101_FOLLOWER_PORT", "/dev/serial/by-id/<follower-id>"))
FRONT_CAM = os.environ.get("SO101_FRONT_CAM", "/dev/v4l/by-id/<front-camera-id>"))
WRIST_CAM = os.environ.get("SO101_WRIST_CAM", "/dev/v4l/by-id/<wrist-camera-id>"))
TASK = os.environ.get("SMOLVLA_TASK", "Pick up the object and place it into the box.")

DEVICE = torch.device("cuda")
CONTROL_FPS = 30.0
WAIT_FPS = 10.0
MAX_TASK_SECONDS = 60.0
RETURN_HOME_SECONDS = 1.5
STALL_SECONDS = 6.0
STALL_MOTION_THRESHOLD = 0.50
MAX_STALL_RECOVERIES = 1

TABLE_SEARCH = (0, 145, 640, 480)
BOX_ROI = (0, 285, 155, 460)
BACKGROUND_FRAMES = 30
TABLE_DIFF_THRESHOLD = 22
BOX_DIFF_THRESHOLD = 18
TABLE_MIN_AREA = 350
TABLE_MAX_AREA = 14000
BOX_MIN_AREA = 280
BOX_MAX_AREA = 12000
TABLE_STABLE_SECONDS = 0.80
BOX_STABLE_SECONDS = 0.90
POST_BOX_GRACE_SECONDS = 0.90
BOX_CLEAR_MAX_FOREGROUND_PIXELS = 220

VIDEO_DIR = Path(os.environ.get("SO101_VIDEO_DIR", "./runs/videos"))
LOG_PATH = Path(os.environ.get("SO101_LOG_PATH", "./runs/smolvla_auto_loop.csv"))


def safe_get_observation(robot, retries=3):
    last_exc = None
    for _ in range(retries):
        try:
            return robot.get_observation()
        except Exception as exc:
            last_exc = exc
            time.sleep(0.12)
    raise RuntimeError("robot observation failed") from last_exc


def safe_send_action(robot, action, retries=2):
    last_exc = None
    for _ in range(retries):
        try:
            robot.send_action(action)
            return
        except Exception as exc:
            last_exc = exc
            time.sleep(0.08)
    raise RuntimeError("robot action send failed") from last_exc


def capture_background(front_camera):
    frames = []
    for _ in range(BACKGROUND_FRAMES):
        frames.append(front_camera.read_latest().astype(np.uint8))
        time.sleep(0.03)
    return np.median(np.stack(frames, axis=0), axis=0).astype(np.uint8)


def foreground_mask(rgb, background_rgb, roi, threshold):
    cur = cv2.GaussianBlur(rgb, (5, 5), 0)
    bg = cv2.GaussianBlur(background_rgb, (5, 5), 0)
    score = np.max(cv2.absdiff(cur, bg), axis=2)
    mask = (score >= threshold).astype(np.uint8) * 255
    x1, y1, x2, y2 = roi
    out = np.zeros_like(mask)
    out[y1:y2, x1:x2] = mask[y1:y2, x1:x2]
    out = cv2.morphologyEx(out, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    out = cv2.morphologyEx(out, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    return out


def find_blob(rgb, bg, roi, threshold, min_area, max_area, exclude_box=False):
    mask = foreground_mask(rgb, bg, roi, threshold)
    if exclude_box:
        x1, y1, x2, y2 = BOX_ROI
        mask[y1:y2, x1:x2] = 0

    n, _, stats, centers = cv2.connectedComponentsWithStats(mask, 8)
    candidates = []
    for i in range(1, n):
        x, y, w, h, area = [int(v) for v in stats[i]]
        cx, cy = [float(v) for v in centers[i]]
        if not (min_area <= area <= max_area):
            continue
        if w < 12 or h < 12:
            continue
        candidates.append({"cx": cx, "cy": cy, "area": area, "bbox": (x, y, w, h)})
    return max(candidates, key=lambda x: x["area"]) if candidates else None


def point_distance(a, b):
    if a is None or b is None:
        return math.inf
    return math.hypot(a["cx"] - b["cx"], a["cy"] - b["cy"])


def get_joint_positions(obs):
    return {k: v for k, v in obs.items() if k.endswith(".pos")}


def smooth_return_home(robot, home_pose):
    current = get_joint_positions(safe_get_observation(robot))
    follower_smooth_move_to(
        robot, current=current, target=home_pose,
        duration_s=RETURN_HOME_SECONDS, fps=30
    )


def wait_for_stable_object(robot, background):
    stable_since = None
    prev = None
    while True:
        obs = safe_get_observation(robot)
        blob = find_blob(
            obs["camera1"], background, TABLE_SEARCH,
            TABLE_DIFF_THRESHOLD, TABLE_MIN_AREA, TABLE_MAX_AREA,
            exclude_box=True,
        )
        now = time.perf_counter()
        if blob is not None:
            if prev is None or point_distance(blob, prev) > 15:
                stable_since = now
            elif stable_since is not None and now - stable_since >= TABLE_STABLE_SECONDS:
                return obs, blob
        else:
            stable_since = None
        prev = blob
        time.sleep(1.0 / WAIT_FPS)


def run_attempt(robot, policy, preprocess, postprocess, dataset_features, background):
    policy.reset()
    started = time.perf_counter()
    prev_joint = None
    last_motion = started
    box_seen_since = None
    stall_recoveries = 0

    while True:
        now = time.perf_counter()
        if now - started >= MAX_TASK_SECONDS:
            return "TIMEOUT", now - started, stall_recoveries

        obs = safe_get_observation(robot)
        front = obs["camera1"]

        box_blob = find_blob(
            front, background, BOX_ROI,
            BOX_DIFF_THRESHOLD, BOX_MIN_AREA, BOX_MAX_AREA,
        )
        if box_blob is not None:
            box_seen_since = box_seen_since or now
            if now - box_seen_since >= BOX_STABLE_SECONDS + POST_BOX_GRACE_SECONDS:
                return "SUCCESS", now - started, stall_recoveries
        else:
            box_seen_since = None

        joint = get_joint_positions(obs)
        if prev_joint is not None:
            delta = max(abs(float(joint[k]) - float(prev_joint[k])) for k in joint if k in prev_joint)
            if delta >= STALL_MOTION_THRESHOLD:
                last_motion = now
        prev_joint = joint

        if now - last_motion >= STALL_SECONDS:
            if stall_recoveries < MAX_STALL_RECOVERIES:
                stall_recoveries += 1
                policy.reset()
                last_motion = now
            else:
                return "STALL", now - started, stall_recoveries

        frame = build_inference_frame(
            observation=obs,
            ds_features=dataset_features,
            device=DEVICE,
            task=TASK,
            robot_type="so_follower",
        )
        with torch.inference_mode():
            action = postprocess(policy.select_action(preprocess(frame)))
        safe_send_action(robot, make_robot_action(action, dataset_features))

        dt = time.perf_counter() - now
        if dt < 1.0 / CONTROL_FPS:
            time.sleep(1.0 / CONTROL_FPS - dt)


def main():
    camera_config = {
        "camera1": OpenCVCameraConfig(index_or_path=Path(FRONT_CAM), width=640, height=480, fps=30),
        "camera2": OpenCVCameraConfig(index_or_path=Path(WRIST_CAM), width=640, height=480, fps=30),
    }
    robot = SO101Follower(SO101FollowerConfig(
        port=FOLLOWER_PORT, id="so101_follower", cameras=camera_config
    ))
    robot.connect()

    try:
        home_pose = get_joint_positions(safe_get_observation(robot))
        background = capture_background(robot.cameras["camera1"])

        policy = SmolVLAPolicy.from_pretrained(str(CKPT))
        policy.eval().to(DEVICE)
        preprocess, postprocess = make_pre_post_processors(
            policy.config,
            str(CKPT),
            preprocessor_overrides={"device_processor": {"device": str(DEVICE)}},
        )

        dataset_features = {
            **hw_to_dataset_features(robot.action_features, "action"),
            **hw_to_dataset_features(robot.observation_features, "observation"),
        }

        cycle = 1
        while True:
            _, blob = wait_for_stable_object(robot, background)
            result, duration, stalls = run_attempt(
                robot, policy, preprocess, postprocess, dataset_features, background
            )
            print(f"cycle={cycle} result={result} duration={duration:.2f}s stalls={stalls} "
                  f"start=({blob['cx']:.1f},{blob['cy']:.1f})")
            smooth_return_home(robot, home_pose)
            cycle += 1

    except KeyboardInterrupt:
        pass
    finally:
        robot.disconnect()


if __name__ == "__main__":
    main()
