
## E5: zombie runs (1320 trials where the stall happened)

| pattern   | guard     |   trials |   fenced |   zombie_errors |   with_loss |   with_dup |   mean_lost |   mean_dup |   correct |
|:----------|:----------|---------:|---------:|----------------:|------------:|-----------:|------------:|-----------:|----------:|
| A1        | none      |       60 |        0 |               0 |           0 |         60 |         0   |      149.6 |         0 |
| A1        | monotonic |       60 |        0 |               0 |           0 |         60 |         0   |       75.9 |         0 |
| A1        | cas       |       60 |       60 |               0 |           0 |         60 |         0   |       75.9 |         0 |
| A2        | none      |       60 |        0 |               0 |           0 |         30 |         0   |       74.8 |        30 |
| A2        | monotonic |       60 |        0 |               0 |           0 |         30 |         0   |       38   |        30 |
| A2        | cas       |       60 |       30 |               0 |           0 |          0 |         0   |        0   |        60 |
| A4        | none      |       30 |        0 |               0 |           0 |         30 |         0   |      149.6 |         0 |
| A4        | monotonic |       30 |        0 |               0 |           0 |         30 |         0   |       75.9 |         0 |
| A4        | cas       |       30 |       30 |               0 |           0 |          0 |         0   |        0   |        30 |
| M1        | none      |       60 |        0 |               0 |           0 |          0 |         0   |        0   |        60 |
| M1        | monotonic |       60 |        0 |               0 |           0 |          0 |         0   |        0   |        60 |
| M1        | cas       |       60 |       60 |               0 |           0 |          0 |         0   |        0   |        60 |
| M2        | none      |       30 |        0 |               0 |           0 |          0 |         0   |        0   |        30 |
| M2        | monotonic |       30 |        0 |               0 |           0 |          0 |         0   |        0   |        30 |
| M2        | cas       |       30 |       30 |               0 |           0 |          0 |         0   |        0   |        30 |
| P1        | none      |       90 |        0 |               0 |           0 |         30 |         0   |       25.4 |        60 |
| P1        | monotonic |       90 |        0 |               0 |          30 |         30 |        22.3 |       28.1 |        30 |
| P1        | cas       |       90 |       90 |               0 |          30 |         30 |        22.3 |       28.1 |        30 |
| P2        | none      |       30 |        0 |               0 |           0 |          0 |         0   |        0   |        30 |
| P2        | monotonic |       30 |        0 |               0 |          30 |          0 |        66.8 |        0   |         0 |
| P2        | cas       |       30 |       30 |               0 |           0 |          0 |         0   |        0   |        30 |
| F1        | none      |       60 |        0 |               0 |           0 |         60 |         0   |      149.6 |         0 |
| F2        | none      |       90 |        0 |              30 |           0 |          0 |         0   |        0   |        90 |
| F4        | none      |       90 |       90 |               0 |           0 |          0 |         0   |        0   |        90 |

## E5 by stall point

| pattern   | guard     | stall_point         |   n |   bad |   fenced |   mean_lost |   mean_dup |
|:----------|:----------|:--------------------|----:|------:|---------:|------------:|-----------:|
| A1        | none      | after_extract       |  30 |    30 |        0 |         0   |      149.6 |
| A1        | none      | after_data_commit   |  30 |    30 |        0 |         0   |      149.6 |
| A1        | monotonic | after_extract       |  30 |    30 |        0 |         0   |       75.9 |
| A1        | monotonic | after_data_commit   |  30 |    30 |        0 |         0   |       75.9 |
| A1        | cas       | after_extract       |  30 |    30 |       30 |         0   |       75.9 |
| A1        | cas       | after_data_commit   |  30 |    30 |       30 |         0   |       75.9 |
| A2        | none      | after_extract       |  30 |    30 |        0 |         0   |      149.6 |
| A2        | none      | after_wm_commit     |  30 |     0 |        0 |         0   |        0   |
| A2        | monotonic | after_extract       |  30 |    30 |        0 |         0   |       75.9 |
| A2        | monotonic | after_wm_commit     |  30 |     0 |        0 |         0   |        0   |
| A2        | cas       | after_extract       |  30 |     0 |       30 |         0   |        0   |
| A2        | cas       | after_wm_commit     |  30 |     0 |        0 |         0   |        0   |
| A4        | none      | after_extract       |  30 |    30 |        0 |         0   |      149.6 |
| A4        | monotonic | after_extract       |  30 |    30 |        0 |         0   |       75.9 |
| A4        | cas       | after_extract       |  30 |     0 |       30 |         0   |        0   |
| M1        | none      | after_extract       |  30 |     0 |        0 |         0   |        0   |
| M1        | none      | after_data_commit   |  30 |     0 |        0 |         0   |        0   |
| M1        | monotonic | after_extract       |  30 |     0 |        0 |         0   |        0   |
| M1        | monotonic | after_data_commit   |  30 |     0 |        0 |         0   |        0   |
| M1        | cas       | after_extract       |  30 |     0 |       30 |         0   |        0   |
| M1        | cas       | after_data_commit   |  30 |     0 |       30 |         0   |        0   |
| M2        | none      | after_extract       |  30 |     0 |        0 |         0   |        0   |
| M2        | monotonic | after_extract       |  30 |     0 |        0 |         0   |        0   |
| M2        | cas       | after_extract       |  30 |     0 |       30 |         0   |        0   |
| P1        | none      | after_extract       |  30 |     0 |        0 |         0   |        0   |
| P1        | none      | after_delete_commit |  30 |    30 |        0 |         0   |       76.1 |
| P1        | none      | after_insert_commit |  30 |     0 |        0 |         0   |        0   |
| P1        | monotonic | after_extract       |  30 |    30 |        0 |        66.8 |        0   |
| P1        | monotonic | after_delete_commit |  30 |    30 |        0 |         0   |       84.2 |
| P1        | monotonic | after_insert_commit |  30 |     0 |        0 |         0   |        0   |
| P1        | cas       | after_extract       |  30 |    30 |       30 |        66.8 |        0   |
| P1        | cas       | after_delete_commit |  30 |    30 |       30 |         0   |       84.2 |
| P1        | cas       | after_insert_commit |  30 |     0 |       30 |         0   |        0   |
| P2        | none      | after_extract       |  30 |     0 |        0 |         0   |        0   |
| P2        | monotonic | after_extract       |  30 |    30 |        0 |        66.8 |        0   |
| P2        | cas       | after_extract       |  30 |     0 |       30 |         0   |        0   |
| F1        | none      | after_extract       |  30 |    30 |        0 |         0   |      149.6 |
| F1        | none      | after_file_write    |  30 |    30 |        0 |         0   |      149.6 |
| F2        | none      | after_extract       |  30 |     0 |        0 |         0   |        0   |
| F2        | none      | after_file_write    |  30 |     0 |        0 |         0   |        0   |
| F2        | none      | after_manifest_tmp  |  30 |     0 |        0 |         0   |        0   |
| F4        | none      | after_extract       |  30 |     0 |       30 |         0   |        0   |
| F4        | none      | after_file_write    |  30 |     0 |       30 |         0   |        0   |
| F4        | none      | after_log_tmp       |  30 |     0 |       30 |         0   |        0   |

## E5b: zombie runs with commit-horizon extraction (300 trials)

| pattern   | guard     |   trials |   correct |   fenced |   with_loss |   with_dup |
|:----------|:----------|---------:|----------:|---------:|------------:|-----------:|
| A4        | none      |       30 |         6 |        0 |           0 |         24 |
| A4        | monotonic |       30 |         6 |        0 |           0 |         24 |
| A4        | cas       |       30 |        30 |       24 |           0 |          0 |
| M2        | none      |       30 |        30 |        0 |           0 |          0 |
| M2        | monotonic |       30 |        30 |        0 |           0 |          0 |
| M2        | cas       |       30 |        30 |       24 |           0 |          0 |
| P2        | none      |       30 |        30 |        0 |           0 |          0 |
| P2        | monotonic |       30 |        18 |        0 |          12 |          0 |
| P2        | cas       |       30 |        30 |       24 |           0 |          0 |
| F4        | none      |       30 |        30 |       30 |           0 |          0 |

## E6: watermark strategies (420 trials)

| lag_dist   |   p_lag | strategy          |   loss_pct |   runs_with_loss |   dup_pct |   read_amp |   lat_p50 |   lat_p99 |   lat_max |   n |
|:-----------|--------:|:------------------|-----------:|-----------------:|----------:|-----------:|----------:|----------:|----------:|----:|
| uniform    |    0.02 | gt                |      1.321 |               10 |         0 |      0.987 |       4.3 |       9   |         9 |  10 |
| uniform    |    0.1  | gt                |      7.051 |               10 |         0 |      0.929 |       4.2 |       9   |         9 |  10 |
| lognormal  |    0.02 | gt                |      1.028 |               10 |         0 |      0.99  |       4.4 |       9   |         9 |  10 |
| lognormal  |    0.1  | gt                |      5.037 |               10 |         0 |      0.95  |       4.2 |       9   |         9 |  10 |
| pareto     |    0.02 | gt                |      0.591 |               10 |         0 |      0.994 |       4.3 |       9   |         9 |  10 |
| pareto     |    0.1  | gt                |      3.465 |               10 |         0 |      0.965 |       4.3 |       9   |         9 |  10 |
| uniform    |    0.02 | lookback 15       |      0     |                0 |         0 |      2.449 |       4.3 |       9   |         9 |  10 |
| uniform    |    0.1  | lookback 15       |      0     |                0 |         0 |      2.389 |       4.3 |       9   |         9 |  10 |
| lognormal  |    0.02 | lookback 15       |      0.099 |                9 |         0 |      2.438 |       4.6 |       9   |         9 |  10 |
| lognormal  |    0.1  | lookback 15       |      0.496 |               10 |         0 |      2.389 |       4.6 |       9   |         9 |  10 |
| pareto     |    0.02 | lookback 15       |      0.048 |                3 |         0 |      2.465 |       4.3 |       9   |         9 |  10 |
| pareto     |    0.1  | lookback 15       |      0.322 |               10 |         0 |      2.417 |       4.3 |       9   |         9 |  10 |
| uniform    |    0.02 | lookback 30       |      0     |                0 |         0 |      3.85  |       4.3 |       9   |         9 |  10 |
| uniform    |    0.1  | lookback 30       |      0     |                0 |         0 |      3.782 |       4.3 |       9   |         9 |  10 |
| lognormal  |    0.02 | lookback 30       |      0.046 |                3 |         0 |      3.848 |       4.6 |       9   |         9 |  10 |
| lognormal  |    0.1  | lookback 30       |      0.162 |                9 |         0 |      3.793 |       4.6 |       9   |         9 |  10 |
| pareto     |    0.02 | lookback 30       |      0.006 |                1 |         0 |      3.86  |       4.3 |       9   |         9 |  10 |
| pareto     |    0.1  | lookback 30       |      0.179 |               10 |         0 |      3.815 |       4.3 |       9   |         9 |  10 |
| uniform    |    0.02 | lookback 60       |      0     |                0 |         0 |      6.48  |       4.3 |       9   |         9 |  10 |
| uniform    |    0.1  | lookback 60       |      0     |                0 |         0 |      6.407 |       4.3 |       9   |         9 |  10 |
| lognormal  |    0.02 | lookback 60       |      0     |                0 |         0 |      6.48  |       4.6 |       9   |         9 |  10 |
| lognormal  |    0.1  | lookback 60       |      0     |                0 |         0 |      6.421 |       4.6 |       9   |         9 |  10 |
| pareto     |    0.02 | lookback 60       |      0.006 |                1 |         0 |      6.489 |       4.3 |       9   |         9 |  10 |
| pareto     |    0.1  | lookback 60       |      0.072 |                5 |         0 |      6.439 |       4.3 |       9   |         9 |  10 |
| uniform    |    0.02 | adaptive lookback |      0.174 |                7 |         0 |      2.445 |       4.3 |       9   |         9 |  10 |
| uniform    |    0.1  | adaptive lookback |      0.263 |               10 |         0 |      3.249 |       4.3 |       9   |         9 |  10 |
| lognormal  |    0.02 | adaptive lookback |      0.25  |               10 |         0 |      1.98  |       4.6 |       9   |         9 |  10 |
| lognormal  |    0.1  | adaptive lookback |      0.456 |               10 |         0 |      3.99  |       4.6 |       9   |        36 |  10 |
| pareto     |    0.02 | adaptive lookback |      0.07  |                5 |         0 |      1.697 |       4.3 |       9   |         9 |  10 |
| pareto     |    0.1  | adaptive lookback |      0.342 |               10 |         0 |      2.424 |       4.3 |       9   |         9 |  10 |
| uniform    |    0.02 | horizon (M2)      |      0     |                0 |         0 |      0.995 |       6.2 |      19.3 |        24 |  10 |
| uniform    |    0.1  | horizon (M2)      |      0     |                0 |         0 |      0.972 |      11.4 |      21.9 |        24 |  10 |
| lognormal  |    0.02 | horizon (M2)      |      0     |                0 |         0 |      0.992 |       6   |      33   |        58 |  10 |
| lognormal  |    0.1  | horizon (M2)      |      0     |                0 |         0 |      0.974 |      12.7 |      46.9 |        69 |  10 |
| pareto     |    0.02 | horizon (M2)      |      0     |                0 |         0 |      0.934 |      15.9 |      44   |       303 |  10 |
| pareto     |    0.1  | horizon (M2)      |      0     |                0 |         0 |      0.947 |      25.7 |     100.4 |       282 |  10 |
| uniform    |    0.02 | horizon (A4)      |      0     |                0 |         0 |      0.995 |       6.2 |      19.3 |        24 |  10 |
| uniform    |    0.1  | horizon (A4)      |      0     |                0 |         0 |      0.972 |      11.4 |      21.9 |        24 |  10 |
| lognormal  |    0.02 | horizon (A4)      |      0     |                0 |         0 |      0.992 |       6   |      33   |        58 |  10 |
| lognormal  |    0.1  | horizon (A4)      |      0     |                0 |         0 |      0.974 |      12.7 |      46.9 |        69 |  10 |
| pareto     |    0.02 | horizon (A4)      |      0     |                0 |         0 |      0.934 |      15.9 |      44   |       303 |  10 |
| pareto     |    0.1  | horizon (A4)      |      0     |                0 |         0 |      0.947 |      25.7 |     100.4 |       282 |  10 |

## E7: horizon extraction with crashes (390 trials, Pareto lag, 10% late)

| pattern   |   trials |   crash_fired |   correct |   with_dup |   with_loss |   corrupt |   transient_bad |
|:----------|---------:|--------------:|----------:|-----------:|------------:|----------:|----------------:|
| A4        |       90 |            90 |        90 |          0 |           0 |         0 |               0 |
| F2        |      150 |           139 |       150 |          0 |           0 |         0 |               0 |
| F4        |      150 |           139 |       150 |          0 |           0 |         0 |               0 |

## E7 by crash point

| pattern   | crash_point        |   n |   correct |   mean_dup |   corrupt |
|:----------|:-------------------|----:|----------:|-----------:|----------:|
| A4        | after_extract      |  30 |        30 |          0 |         0 |
| A4        | mid_txn            |  30 |        30 |          0 |         0 |
| A4        | after_commit       |  30 |        30 |          0 |         0 |
| F2        | after_extract      |  30 |        30 |          0 |         0 |
| F2        | mid_file_write     |  30 |        30 |          0 |         0 |
| F2        | after_file_write   |  30 |        30 |          0 |         0 |
| F2        | after_manifest_tmp |  30 |        30 |          0 |         0 |
| F2        | after_commit       |  30 |        30 |          0 |         0 |
| F4        | after_extract      |  30 |        30 |          0 |         0 |
| F4        | mid_file_write     |  30 |        30 |          0 |         0 |
| F4        | after_file_write   |  30 |        30 |          0 |         0 |
| F4        | after_log_tmp      |  30 |        30 |          0 |         0 |
| F4        | after_commit       |  30 |        30 |          0 |         0 |