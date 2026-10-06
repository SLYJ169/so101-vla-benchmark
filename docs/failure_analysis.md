# Failure Analysis

本项目不仅看最终完成率，也分析失败模式如何随模型变化。

## ACT

ACT 的最终失败大多集中在一个局部 weak region，主要表现为：

- 抓取位置偏差；
- 夹爪闭合时机或位置不理想；
- 抓取稳定性不足。

## SmolVLA

SmolVLA 对工作空间内部位置的覆盖更好，剩余失败更多出现在：

- 工作空间边界；
- reach limit；
- contact limit。

## π0.5

π0.5 进一步覆盖了大多数此前困难位置，第二组正式 20 次测试中仅剩 1 次极端 reach/contact case。

## 总体演化

~~~text
ACT
内部局部 weak region
        ↓
SmolVLA
内部位置覆盖改善
失败转向 workspace/contact limit
        ↓
π0.5
大部分边界困难样本被覆盖
仅剩极端 reach/contact case
~~~