# Scripts

这里保存的是本项目特有的 orchestration / evaluation 脚本，而不是复制上游模型实现。

- `continuous_pick/smolvla_auto_pick_loop.py`：SmolVLA 连续自主抓取 Task Manager 的公开清理版。
- `evaluation/summarize_trials.py`：按 Final Completion 汇总测试 CSV。

ACT 与 SmolVLA 模型主体来自 LeRobot；π0.5 训练和推理主体来自 OpenPI。

大体积 checkpoint、原始数据、云端敏感路径和连接信息不进入 Git。