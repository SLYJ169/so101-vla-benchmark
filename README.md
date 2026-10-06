# SO-101 多模型 VLA 真机 Benchmark

基于同一套 **SO-101 + Front/Wrist 双相机**平台和同一份 Final50 数据，对 **ACT、SmolVLA、π0.5** 完成训练/微调、真机部署和统一 20 次自动执行测试。

任务：**从桌面抓取红色目标并放入盒子**。

| 项目 | 配置 |
|---|---|
| Robot | SO-101 Leader / Follower |
| Cameras | Front + Wrist |
| Dataset | Final50：50 episodes / 14,753 frames |
| Task | Pick up the red object and place it into the box. |
| Models | ACT / SmolVLA / π0.5 |

---

## Demo

展示不同桌面位置下的 **接近目标 → 抓取 → 搬运 → 放入盒子** 完整过程。点击动图可查看完整 MP4。

<table>
<tr>
<td align="center"><b>ACT</b><br><a href="assets/demos/act_best_demo.mp4"><img src="assets/demos/act_best_demo.webp" width="300"></a></td>
<td align="center"><b>SmolVLA</b><br><a href="assets/demos/smolvla_best_demo.mp4"><img src="assets/demos/smolvla_best_demo.webp" width="300"></a></td>
<td align="center"><b>π0.5</b><br><a href="assets/demos/pi05_best_demo.mp4"><img src="assets/demos/pi05_best_demo.webp" width="300"></a></td>
</tr>
</table>

### π0.5 未见物体测试

额外测试了更小的蓝紫色小鸭和胶带类物体，展示未见物体下的定位、抓取和放置过程。

[![π0.5 OOD Demo](assets/demos/pi05_ood_tape_demo.webp)](assets/demos/pi05_ood_tape_demo.mp4)

蓝紫色小鸭尺寸更小，实际测试中更容易出现抓取失败；胶带类物体可以完成抓取和放置。目标外观和位置变化时，π0.5 仍能继续执行任务，但尺寸和几何形状变化会明显影响抓取点和夹爪闭合。

---

## 真机结果

每个模型执行 20 次自动任务，以**最终是否将目标放入盒子**作为成功判据。

| 模型 | Checkpoint | 完成率 |
|---|---:|---:|
| ACT | 80k | **15/20（75%）** |
| SmolVLA | 20k | **17/20（85%）** |
| π0.5 | 6000 updates / dir 5999 | **19/20（95%）** |

<p align="center">
  <img src="assets/benchmark/final_completion.svg" width="760">
</p>

> 三组测试使用同一平台、同一任务和同一数据集；测试位置并非逐点一一对应。

---

## 硬件与任务

<p align="center">
  <img src="assets/overview/setup.jpg" width="760">
</p>

机器人输入为 Front + Wrist 两路 RGB 图像和 6D 关节状态，输出 6D 关节动作。

| 组件 | 配置 |
|---|---|
| Robot | SO-101 Leader / Follower |
| Leader | 5 V |
| Follower | 12 V |
| Cameras | Front + Wrist |
| Resolution | 640×480 @ 30 FPS |
| State / Action | 6D / 6D |
| Local | Ubuntu 22.04 + RTX 3060 Laptop 6 GB |
| π0.5 | H800 80 GB |

正式测试使用 `/dev/serial/by-id/` 和 `/dev/v4l/by-id/` 固定机械臂与相机设备路径，避免 USB 编号变化。

更多硬件记录见 [docs/hardware.md](docs/hardware.md)。

---

## Final50

三种模型统一使用冻结后的 Final50。

| 项目 | 数值 |
|---|---:|
| Episodes | **50** |
| Frames | **14,753** |
| FPS | **30** |
| Cameras | Front + Wrist |
| Image | 480×640 |
| State / Action | 6D / 6D |

数据来自多位置遥操作。录制后逐条检查 episode，删除不合格数据并补录至 50 条，之后冻结数据版本，三种模型均使用同一份数据。

任务文本：

~~~text
Pick up the red object and place it into the box.
~~~

详细记录见 [docs/dataset.md](docs/dataset.md)。

---

## ACT

- Checkpoint：**80k**
- Batch size：8
- Dataset：Final50
- 真机结果：**15/20**

配置：[`configs/act.yaml`](configs/act.yaml)

---

## SmolVLA

- Base model：`lerobot/smolvla_base`
- Training：20k steps
- Batch size：32
- Seed：1000
- 真机结果：**17/20**

另外实现了连续自主抓取流程：桌面出现新目标后自动启动策略，目标进入盒子后回到 Home，并等待下一次任务。目标检测、timeout/stall 处理和连续录像作为独立 Task Manager 运行，不改动正式 20-trial 的 policy loop。

配置：[`configs/smolvla.yaml`](configs/smolvla.yaml)  
脚本：[`scripts/continuous_pick/smolvla_auto_pick_loop.py`](scripts/continuous_pick/smolvla_auto_pick_loop.py)

---

## π0.5

- Base model：`pi05_base`
- Framework：OpenPI / JAX
- Fine-tuning：Full-Parameter
- GPU：1× H800 80 GB
- Batch size：32
- Action horizon：50
- Updates：6000
- Checkpoint：5999
- 真机结果：**19/20**

训练与 policy server 部署在 H800，本地 SO-101 负责相机采集、机械臂控制和动作执行。

<p align="center">
  <img src="assets/overview/pi05_deployment.svg" width="850">
</p>

~~~text
Front + Wrist + state
        ↓
SO-101 local client
        ↓
SSH tunnel / WebSocket
        ↓
H800 OpenPI policy server
        ↓
50×6 action chunk
        ↓
执行前 25 个 action
        ↓
重新观测 / replanning
~~~

正式测试保持该控制链固定，没有额外加入 clipping、smoothing 或 RTC/async。

配置：[`configs/pi05.yaml`](configs/pi05.yaml)

---

## Failure Analysis

| 模型 | 主要失败情况 |
|---|---|
| ACT | 失败较多集中在桌面内部局部区域，主要表现为抓取位置偏差和抓取不稳定 |
| SmolVLA | 内部位置覆盖更好，剩余失败更多出现在工作空间边界及 reach/contact 限制附近 |
| π0.5 | 第二组正式 20 次仅 1 次最终失败，位于极端边界位置 |

详细记录见 [docs/failure_analysis.md](docs/failure_analysis.md)。

---

## 评测与复现

- 三模型结果：[`results/benchmark_summary.csv`](results/benchmark_summary.csv)
- π0.5 正式 20 次记录：[`results/pi05_formal_trial_results.csv`](results/pi05_formal_trial_results.csv)
- 测试协议：[`docs/benchmark_protocol.md`](docs/benchmark_protocol.md)
- OOD 记录：[`docs/ood_evaluation.md`](docs/ood_evaluation.md)
- 部署说明：[`docs/deployment.md`](docs/deployment.md)
- 复现说明：[`docs/reproduction.md`](docs/reproduction.md)

---

## Repository Structure

~~~text
so101-vla-benchmark/
├── assets/
│   ├── benchmark/
│   ├── demos/
│   └── overview/
├── configs/
│   ├── act.yaml
│   ├── smolvla.yaml
│   └── pi05.yaml
├── docs/
├── scripts/
└── results/
~~~

上游项目：

- [LeRobot](https://github.com/huggingface/lerobot) — SO-101、ACT、SmolVLA
- [OpenPI](https://github.com/Physical-Intelligence/openpi) — π0.5
- [ACT](https://github.com/tonyzhaozh/act) — ACT 原始实现

完整数据、模型 checkpoint 和长时间原始录像不直接提交到 Git。