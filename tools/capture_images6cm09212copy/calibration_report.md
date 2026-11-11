# 6cm09212 offline hand-eye calibration

Board model: 5x5 ChArUco, DICT_4X4_50, full pattern 60 mm, square 12 mm, assumed marker 8 mm. Eye-in-hand, stationary board. Actual reported robot poses in metres, Rz*Ry*Rx radians. TCP versus flange frame not independently confirmed.

89 original image/metadata pairs, 86 point IDs. Retained 70 unique points: 58 with 16 corners, 12 with 8-15 corners. Excluded 16 severely cropped points with fewer than 8 detected corners and 3 duplicate captures. First eligible capture per point retained. No residual-based removal merely to improve metrics.

Excluded point IDs: P57-P60, P63-P66, P69-P72, P81-P84.
Duplicates: one additional P51 and two additional P54 captures.
All excluded pairs moved to _excluded/invalid or _excluded/duplicates. Original bytes retained; image hashes verified. Main directory contains 70 selected P*.jpg/P*.json pairs. See excluded_samples.json for paths and reasons.

Main candidate: PARK; handeye_api.json contains pose3d.cameraMatrix, distCoeffs and gTc. handeye_result.json contains complete evidence and comparison of five solver methods. Translation units are metres. Source per-sample observations remain in calibration_sample_audit.json; moved observations can be located using excluded_samples.json.

| Dataset | Samples | Reprojection RMS px | Five-fold position RMS mm | Five-fold orientation RMS deg |
|---|---:|---:|---:|---:|
| Original P01-P50 | 50 | 0.063739 | 0.191455 | 0.056757 |
| Full 16 corners only | 58 | 0.064211 | 0.191409 | 0.057534 |
| All eligible unique points (main) | 70 | 0.066932 | 0.175588 | 0.079709 |

Main training fixed-board consistency: 0.165078 mm RMS, 0.062581 deg RMS. Five-fold P95 position 0.289865 mm, maximum 0.440324 mm; orientation maximum 0.288654 deg. Folds group by point number modulo 5; intrinsics, distortion, hand-eye and board reference fit on training only. Screening occurs before folds. These are internal consistency estimates, not independent physical accuracy.

70-point versus 58-point transform translation differs by 1.732242 mm, rotation by 0.071118 deg. Sample-selection sensitivity remains; the larger sample set is not proven more accurate overall. Added rotations improved internal translation RMS but worsened orientation RMS. Stronger fixed-XYZ tilts moved the board out of view. Do not treat these point candidates as universally valid capture trajectories.

Use only with the same mounting, optical settings and robot reporting frame; collect a new station reference with the new intrinsics before comparing closed-loop runs. No online settings or robot/capture scripts modified. selected_points.json is an inventory of retained target poses, not a motion program; actual_pose_before was used for solving.
