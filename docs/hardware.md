# 硬件平台

## SO-101 真机系统

| 组件 | 配置 |
|---|---|
| Leader | SO-101，5 V |
| Follower | SO-101，12 V |
| Front Camera | RGB，640×480 @ 30 FPS |
| Wrist Camera | RGB，640×480 @ 30 FPS |
| 本地电脑 | Lenovo Legion R9000P，Ubuntu 22.04 |
| 本地 GPU | RTX 3060 Laptop 6 GB |
| π0.5 训练 / Policy Server | NVIDIA H800 80 GB |

Leader 与 Follower 的供电电压不同，调试时必须严格区分，不能交叉使用。

## 稳定设备路径

项目早期遇到过 USB 口与设备编号变化导致的断连问题，因此正式链路不再依赖 `/dev/ttyACM0`、`/dev/video0` 等易变化编号，而优先使用：

- `/dev/serial/by-id/`
- `/dev/v4l/by-id/`

## 双相机

- **Front**：提供桌面、目标和盒子的全局视觉信息；
- **Wrist**：提供近距离抓取和接触信息。

Final50 与正式部署均使用 Front + Wrist 双相机。