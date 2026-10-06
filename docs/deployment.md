# 真机部署

## SO-101

- Front + Wrist RGB
- Follower：12 V
- Leader：5 V
- 稳定串口与相机路径：`/dev/serial/by-id/`、`/dev/v4l/by-id/`

## π0.5 远程 Policy Server

最终部署链路：

~~~text
Front + Wrist observation
        ↓
本地 SO-101 client
        ↓
SSH tunnel / WebSocket
        ↓
H800 OpenPI policy server
        ↓
50×6 absolute action chunk
        ↓
执行前 25 个 action
        ↓
重新观测 / replanning
~~~

控制频率约为 30 Hz。

正式 Benchmark 保持控制链冻结，不额外加入 action clipping、smoothing、secondary transform、RTC 或其他会改变 policy 行为的逻辑。