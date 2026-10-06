# π0.5 OOD / 泛化测试

π0.5 额外测试了训练中未出现的物体，包括：

- 更小的蓝紫色小鸭；
- 胶带类物体；
- 其他尺寸、形状、颜色明显变化的目标。

这些测试属于 qualitative exploration，不作为正式 20-trial Benchmark。

最准确的项目结论是：

> **有限的跨物体 visuomotor generalization；perception/task-level generalization 强于 geometry-conditioned grasp generalization。**

即：π0.5 往往能够判断“哪个是目标、目标在哪里、应该执行抓取任务”，但对于未见尺寸/形状，其 grasp pose、contact point 和 closure strategy 的自适应仍有限。

因此本项目不声称：

- 能抓任意新物体；
- 已具备通用抓取策略；
- 能自动理解所有物体的最优抓取姿态。