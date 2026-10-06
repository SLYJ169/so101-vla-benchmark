# 复现说明

## 1. 硬件

SO-101 Leader/Follower：

- Leader：5 V
- Follower：12 V
- Front + Wrist 双相机
- 640×480 @ 30 FPS
- 建议使用 `/dev/serial/by-id/` 与 `/dev/v4l/by-id/` 固定设备路径

## 2. 数据

任务指令：

~~~text
Pick up the red object and place it into the box.
~~~

Final50：

- 50 episodes
- 14,753 frames
- Front + Wrist
- state/action = 6D/6D

## 3. 训练

配置文件：

- `configs/act.yaml`
- `configs/smolvla.yaml`
- `configs/pi05.yaml`

模型实现来自上游：

- LeRobot：ACT、SmolVLA、SO-101 接口
- OpenPI：π0.5

## 4. Checkpoint Selection

Checkpoint 选择以真机 rollout 为准。ACT 的正式 checkpoint 为 80k；SmolVLA 为 20k；π0.5 为 6000 updates / dir 5999。

## 5. 真机评测

每个模型执行 20 次自动任务，以最终是否将目标放入盒子作为成功判据。

## 6. π0.5 部署

~~~text
Front + Wrist
→ local SO-101 client
→ SSH/WebSocket
→ H800 OpenPI server
→ 50×6 action chunk
→ execute first 25
→ re-observe / replan
~~~

正式 Benchmark 未加入 clipping、smoothing 或 RTC/async。