# 复现说明

本仓库用于记录完整工程链路，但不会直接发布大体积 checkpoint 与全部原始视频。

## 1. 硬件

准备 SO-101 Leader/Follower：

- Leader 5 V
- Follower 12 V
- Front + Wrist 双相机
- 640×480 @ 30 FPS
- 建议使用稳定 `/dev/serial/by-id/` 与 `/dev/v4l/by-id/` 路径

## 2. 数据

任务指令：

~~~text
Pick up the red object and place it into the box.
~~~

本项目冻结数据集：

- 50 episodes
- 14,753 frames
- Front + Wrist
- state/action = 6D/6D

## 3. 训练

核心配置位于：

- `configs/act.yaml`
- `configs/smolvla.yaml`
- `configs/pi05.yaml`

模型实现来自上游：

- LeRobot：ACT、SmolVLA、SO-101 接口
- OpenPI：π0.5

## 4. Checkpoint Selection

不要只看 training loss。ACT 100k loss 更低但真机不如 80k，是本项目中最直接的例子。

## 5. 真机评测

每个模型执行 20 次自动任务，并记录最终是否完成放置。

本仓库首页只展示 Final Completion。

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

正式 Benchmark 不加入 clipping、smoothing 或 RTC/async。