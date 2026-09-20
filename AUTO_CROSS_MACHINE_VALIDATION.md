# 跨工位自动视觉闭环验证

适用同一套 AGV/机械臂/相机在不同工位移动。参考图与当前图必须使用相同的相机、镜头、分辨率、相机安装和标定板几何规格。不同相机的跨设备几何迁移尚不支持。更换标定参数后应重新采集基准。

本脚本不重新求解手眼；固定 handeye/reference，测试补偿、运动、复拍的闭环表现。`VISUAL_PASS` 仅表示视觉残差达标，不是独立量具测得的实际定位精度。PLC 的实际位姿也不是独立计量真值。

## 使用

原 `collect-reference` 和 `check-profile` 命令保持可用。已有 profile 可以继续使用。

在项目目录、已配置依赖的环境中，重复 5 轮（此命令会执行真实运动）：

```powershell
python auto_cross_machine_calibration.py run --profile cross_machine_station_001.json --rounds 5 --confirm-same-camera --confirm-single-pose-task --execute
```

每轮重新从 observation_pose 开始；每次补偿后的运动仍沿用返回、再次下发目标的 PLC 握手。未收敛且已正常返回时继续下一轮；通信、运动、安全范围或视觉异常时终止整次测试，不追加清零或运动。

可选 `--offsets-json offsets.json` 指定起始偏移：

```json
{"offsets": [[0,0,0,0,0,0], [0.005,0,0,0,0,0], [-0.005,0,0,0,0,0]]}
```

XYZ 是基坐标系平移分量，单位 m；后三项是欧拉角分量增量，单位 rad。相对于 observation_pose 构造初始目标；不改变参考目标。上例配合 `--rounds 5` 为 15 个独立轮次。所有偏移在连接设备前检查范围；现场仍需确认机械臂完整运动路径。默认不加偏移、只测一轮。

`--handeye-json` 现在仅接受与基准 profile 几何参数完全一致的文件，不再静默替换不同设备标定。

## 报告

报告 schema_version 升为 2，最终状态为 `VISUAL_PASS`、`FAIL_NOT_CONVERGED` 或 `ABORTED`。消费者需更新原 `PASS` 判断及顶层最终结果字段读取。

- `effective_profile`：生效参数完整快照；另存源 profile 哈希、参考采集信息和 health 响应。health 只提供配置路径等信息，不证明设备身份；`--confirm-same-camera` 是操作员声明。
- `trials`：每轮初始目标、补偿次数、所有观测及最终目标。
- `initial`：补偿前首次观测。
- `after_first_correction`：执行一次补偿后的首次观测；未执行补偿时为 null，不虚构样本。
- `final`：最终一次验收观测，包含未收敛轮次；同位连续复拍保留在 observations，不增加统计样本数。
- `summary`：上述三个阶段分别统计 X/Y/Z、XY、XYZ（mm）、总旋转（deg）的 RMS、绝对值 P95、最大绝对值和样本数；统计完成、通过、未收敛、中止数量及计划轮次通过率。中止轮次未完成的阶段不进入统计。

所有精度字段都是视觉预测剩余补偿量。评估实际作业精度时，另需独立量具/治具测量并与 trial_index 对应。

离线验证（不连接设备）：

```powershell
python -B -m unittest test_auto_cross_machine_calibration -v
python -B auto_cross_machine_calibration.py self-test
```
