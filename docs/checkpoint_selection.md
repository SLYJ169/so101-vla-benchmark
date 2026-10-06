# Checkpoint 筛选

最终 checkpoint 以真机 rollout 表现为准。

## ACT

ACT 训练到 100k，保存 20k / 40k / 60k / 80k / 100k checkpoint。

100k 的训练 loss 更低，但 80k 在真机测试中表现更好，因此正式 Benchmark 使用 80k。

## SmolVLA

SmolVLA 训练到 20k，正式 20-trial 使用 20k checkpoint。

5k / 10k / 15k / 20k 没有全部做完整 20-trial 横向测试，因此 20k 作为本项目的正式 baseline。

## π0.5

开发阶段比较了 3000 / 4000 / 5000 / 6000 updates，最终使用 **6000 updates / checkpoint dir 5999**。

正式结果来自第二组 clean 20-trial。