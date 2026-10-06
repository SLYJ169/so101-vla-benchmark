# Checkpoint 筛选

本项目的最终 checkpoint 选择以**真实机器人 rollout 表现**为主要依据，而不是只看训练 loss。

## ACT

ACT 训练到 100k，并保存 20k / 40k / 60k / 80k / 100k。

关键现象：**100k 的训练 loss 更低，但 80k 真机表现更好。**

因此正式 ACT 使用 80k。

## SmolVLA

SmolVLA 训练到 20k，正式 20-trial 使用 20k checkpoint。

这里不夸大为“20k 一定是全局最优”，更准确的说法是：20k 是已经完成正式 20-trial 的冻结 baseline。

## π0.5

π0.5 在开发阶段逐步比较多个训练进度，最终选择 **6000 updates / checkpoint dir 5999**。

正式主结果使用第二组 clean 20-trial。