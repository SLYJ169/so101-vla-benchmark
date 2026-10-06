# Final50 数据集

Final50 是 P1 三个模型统一使用的冻结数据集。

## 数据统计

- 50 episodes
- 14,753 frames
- 30 FPS
- Front + Wrist 双相机
- 图像（H×W）480×640
- state = 6D
- action = 6D
- robot_type = SO-101 follower

冻结任务文本：

~~~text
Pick up the red object and place it into the box.
~~~

## 数据清洗

原始数据覆盖多个目标位置。所有 episode 经过人工审查，不合格 demonstration 被删除，之后补录至 50 条并冻结为 Final50。

ACT、SmolVLA、π0.5 主实验均基于该冻结版本，避免为了某个模型的短期表现而反复修改训练集。

完整原始视频与大体积数据不直接提交到 Git 仓库。