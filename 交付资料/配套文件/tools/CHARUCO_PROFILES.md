# 手眼板与工位板配置

实际配置文件由启动参数 `--config` 决定；修改后重启服务。

- `handeye_charuco`：手眼离线批量采样、图片采样和在线采样。
- `station_charuco`：跨机台基准采集、二次补偿图像检测及基准角点物理坐标恢复。

两组均使用原 `charuco` 的字段：`dictionary_name`、`squares_x`、
`squares_y`、`square_length_m`、`marker_length_m` 及各检测参数。
长度单位为米，格子数不是内角点数，标记边长必须小于格子边长。
两块板尺寸可以不同，但应各自准确对应实物。

随附配置初次迁移时，两组分别保留各文件原有的板参数。
`settings.yaml` 中三块新板仍是注释备选；使用时把参数复制到对应的新配置块，
不要直接取消旧 `charuco:` 示例的注释。已存在新配置块时，新配置优先。

旧配置兼容：仅有 `charuco` 时，两组分别复制旧配置；只提供一个新配置块时，
另一个从旧 `charuco` 回退。新配置块不与旧字段逐项混合，缺少的字段使用
`CharucoSettings` 默认值，建议完整填写。显式写为 `null` 会报配置错误。

Java 接口地址和字段保持不变。当前精简工位基准没有完整板规格，视觉会按
`station_charuco` 恢复物理坐标。因此更换工位板尺寸、字典或布局后，必须
重新采集工位基准，并由 Java 保存和回传；本次拆分不提供旧基准规格自动校验。
相机、镜头或安装关系变化时，也应重新进行相应标定与验证。

调试识别可使用 `debug_fail_detect.py --purpose handeye` 或
`--purpose station`，并通过 `--config`、`--image-dir`、`--output-dir` 指定路径。
`check_secondary_board_repeatability.py` 仍是 ArUco 专用检查脚本。

离线回归：`python -m unittest test_charuco_profiles -v`。
合成图像测试不替代相机、机器人及现场精度验证。
