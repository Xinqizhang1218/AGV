-- Reproducible, reviewed snapshot for the 2026-07-31 vs 2026-08-18 report.
-- Values are transcribed from the source JSON files and robot-pose logs listed
-- in reports/handeye_calibration_comparison_metrics.json.
WITH report_data(dataset, record_id, batch, metric, value, value2, text_value, unit) AS (
  VALUES
    ('headline_metrics', 'july_translation_rmse', '2026-07-31', 'translation_rmse_mm', 3.570421, NULL, NULL, 'mm'),
    ('headline_metrics', 'desktop_success_rmse', 'desktop / 2026-07-30', 'translation_rmse_mm', 0.247992, NULL, '23 samples; P01 excluded due to 1004x627 resolution', 'mm'),
    ('headline_metrics', 'august_translation_rmse', '2026-08-18', 'translation_rmse_mm', 0.273783, NULL, NULL, 'mm'),
    ('headline_metrics', 'relative_rotation', 'comparison', 'relative_rotation_deg', 54.370946, NULL, NULL, 'deg'),
    ('headline_metrics', 'relative_translation', 'comparison', 'relative_translation_mm', 85.064254, NULL, NULL, 'mm'),
    ('headline_metrics', 'historical_consistency', '2026-08-18 vs 2026-07-30', 'translation_and_rotation', 3.805091, 0.309676, NULL, 'mm / deg'),
    ('quality', 'camera_rms', '2026-07-31', 'camera_rms_px', 0.165512, NULL, '24 samples; corners 8/14.29/16', 'px'),
    ('quality', 'camera_rms', '2026-08-18', 'camera_rms_px', 0.116017, NULL, '30 samples; corners 16/16/16', 'px'),
    ('quality', 'rotation_rmse', '2026-07-31', 'rotation_rmse_deg', 0.921929, NULL, 'Park; archived quality ok=false', 'deg'),
    ('quality', 'rotation_rmse', '2026-08-18', 'rotation_rmse_deg', 0.111709, NULL, 'Park; no separate quality report', 'deg'),
    ('gtc_translation', 'x', '2026-07-31', 'gTc_x_mm', -89.635345, NULL, NULL, 'mm'),
    ('gtc_translation', 'y', '2026-07-31', 'gTc_y_mm', 10.719874, NULL, NULL, 'mm'),
    ('gtc_translation', 'z', '2026-07-31', 'gTc_z_mm', 96.069448, NULL, NULL, 'mm'),
    ('gtc_translation', 'x', '2026-08-18', 'gTc_x_mm', -132.567131, NULL, NULL, 'mm'),
    ('gtc_translation', 'y', '2026-08-18', 'gTc_y_mm', -55.954000, NULL, NULL, 'mm'),
    ('gtc_translation', 'z', '2026-08-18', 'gTc_z_mm', 65.289851, NULL, NULL, 'mm'),
    ('pose_coverage', 'xyz_span', '2026-07-31', 'xyz_span_mm', 39.570000, 39.762000, 'z=39.268; rotation SVD=25.84/24.66/13.87 deg', 'mm'),
    ('pose_coverage', 'xyz_span', '2026-08-18', 'xyz_span_mm', 30.000959, 40.002440, 'z=10.00748; rotation SVD=21.72/15.61/9.23 deg', 'mm'),
    ('timing', 'capture_window', '2026-08-18', 'duration_s', 161.000000, 6.000000, '11:19:13-11:21:54; request 11:21:56.928', 's'),
    ('field_diagnostic', 'reference_center', 'provided request pair', 'reference_center_delta_px', 70.820473, -5.463318, 'planar magnitude ~=22.98 mm using first reference scale', 'px'),
    ('field_diagnostic', 'reference_scale', 'provided request pair', 'marker_edge_change_percent', -4.567480, NULL, '463.645 px vs 442.468 px mean edge', 'percent'),
    ('field_diagnostic', 'reference_angle', 'provided request pair', 'reference_angle_delta_deg', 1.747775, NULL, NULL, 'deg'),
    ('field_diagnostic', 'flange_input', 'provided request pair', 'flange_position_delta_mm', 14.478653, 1.203211, 'value2 is rz difference in degrees', 'mm / deg'),
    ('field_diagnostic', 'repeat_calls', '2026-08-21', 'repeated_call_count', 26.000000, 38.516000, 'same timestamp and currentFlangePose; value2 is max XY output norm', 'count / mm'),
    ('field_diagnostic', 'reference_drift', '2026-08-21', 'reference_center_range_x_px', 23.302029, 22.708727, '24 calls used one reference and 2 calls used another', 'px'),
    ('capture_quality', 'full_corner_rate', '2026-07-31', 'full_16_corner_rate', 54.166667, 13.000000, '13 of 24 frames had all 16 corners; P23 had 8 corners', 'percent / frames'),
    ('capture_quality', 'full_corner_rate', '2026-08-18', 'full_16_corner_rate', 100.000000, 30.000000, '30 of 30 frames had all 16 corners', 'percent / frames'),
    ('capture_quality', 'error_ratio', 'comparison', 'handeye_vs_camera_degradation_factor', 13.041047, 1.426626, 'value=hand-eye translation RMSE factor; value2=camera RMS factor', 'factor'),
    ('capture_quality', 'plan_exception', '2026-08-18', 'near_duplicate_pose_count', 1.000000, 0.000627, 'P03-P05; value2 is translation difference in mm', 'count / mm'),
    ('batch_identity', 'desktop_hash_match', 'desktop vs 20260730', 'matching_file_count', 24.000000, 24.000000, 'value2 is compared file count; also 24/24 match 20260804 rerun', 'files'),
    ('batch_identity', 'archive_hash_match', 'desktop vs 20260731_170812', 'matching_file_count', 0.000000, 24.000000, 'all archived failure images differ from desktop photos', 'files'),
    ('batch_identity', 'desktop_quality', 'desktop / 20260730', 'full_16_corner_frames', 22.000000, 24.000000, 'corner min/mean/max=14/15.83/16; primary solve excludes P01', 'frames'),
    ('batch_identity', 'desktop_p01', 'desktop / 20260730', 'p01_width_px', 1004.000000, 627.000000, 'other 23 images are 1280x800; P01 excluded', 'px'),
    ('batch_identity', 'desktop_primary_rmse', 'desktop / 20260730', 'translation_rmse_mm', 0.247992, 0.146624, 'value2 is rotation RMSE deg; 23 valid images', 'mm / deg'),
    ('batch_identity', 'desktop_p01_sensitivity', 'desktop / 20260730', 'translation_rmse_mm', 0.577708, 1.439123, 'P01 scaled then included; value2 is rotation RMSE deg', 'mm / deg')
)
SELECT * FROM report_data;
