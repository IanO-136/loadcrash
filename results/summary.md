
## E1: crash-point outcomes (2200 trials, ordered source)

| pattern   | crash_point         |   trials | final       | transient   |   mean_lost |   mean_dup |   mean_storage_overhead |   mean_exp_regression |
|:----------|:--------------------|---------:|:------------|:------------|------------:|-----------:|------------------------:|----------------------:|
| A1        | after_extract       |       50 | ok          | ok          |           0 |        0   |                     0   |                   0   |
| A1        | mid_data_txn        |       50 | ok          | ok          |           0 |        0   |                     0   |                   0   |
| A1        | after_data_commit   |       50 | DUP         | ok          |           0 |       75   |                    75   |                   0   |
| A1        | after_wm_commit     |       50 | ok          | ok          |           0 |        0   |                     0   |                   0   |
| A2        | after_extract       |       50 | ok          | ok          |           0 |        0   |                     0   |                   0   |
| A2        | after_wm_commit     |       50 | LOSS        | ok          |          75 |        0   |                     0   |                   0   |
| A2        | mid_data_txn        |       50 | LOSS        | ok          |          75 |        0   |                     0   |                   0   |
| A2        | after_data_commit   |       50 | ok          | ok          |           0 |        0   |                     0   |                   0   |
| A3        | after_extract       |       50 | ok          | ok          |           0 |        0   |                     0   |                   0   |
| A3        | mid_data_txn        |       50 | ok          | ok          |           0 |        0   |                     0   |                   0   |
| A3        | after_data_commit   |       50 | ok          | ok          |           0 |        0   |                    75   |                   0   |
| A3        | after_wm_commit     |       50 | ok          | ok          |           0 |        0   |                     0   |                   0   |
| A4        | after_extract       |       50 | ok          | ok          |           0 |        0   |                     0   |                   0   |
| A4        | mid_txn             |       50 | ok          | ok          |           0 |        0   |                     0   |                   0   |
| A4        | after_commit        |       50 | ok          | ok          |           0 |        0   |                     0   |                   0   |
| M1        | after_extract       |       50 | ok          | ok          |           0 |        0   |                     0   |                   0   |
| M1        | mid_data_txn        |       50 | ok          | ok          |           0 |        0   |                     0   |                   0   |
| M1        | after_data_commit   |       50 | ok          | ok          |           0 |        0   |                     0   |                   0   |
| M1        | after_wm_commit     |       50 | ok          | ok          |           0 |        0   |                     0   |                   0   |
| M2        | after_extract       |       50 | ok          | ok          |           0 |        0   |                     0   |                   0   |
| M2        | mid_txn             |       50 | ok          | ok          |           0 |        0   |                     0   |                   0   |
| M2        | after_commit        |       50 | ok          | ok          |           0 |        0   |                     0   |                   0   |
| P1        | after_extract       |       50 | ok          | ok          |           0 |        0   |                     0   |                   0   |
| P1        | after_delete_commit |       50 | ok          | regress     |           0 |        0   |                     0   |                   7.8 |
| P1        | mid_insert_txn      |       50 | ok          | regress     |           0 |        0   |                     0   |                   7.8 |
| P1        | after_insert_commit |       50 | ok          | ok          |           0 |        0   |                     0   |                   0   |
| P1        | after_wm_commit     |       50 | ok          | ok          |           0 |        0   |                     0   |                   0   |
| P2        | after_extract       |       50 | ok          | ok          |           0 |        0   |                     0   |                   0   |
| P2        | mid_txn             |       50 | ok          | ok          |           0 |        0   |                     0   |                   0   |
| P2        | after_commit        |       50 | ok          | ok          |           0 |        0   |                     0   |                   0   |
| F1        | after_extract       |       50 | ok          | ok          |           0 |        0   |                     0   |                   0   |
| F1        | mid_file_write      |       50 | DUP+CORRUPT | unreadable  |           0 |        4.6 |                     4.6 |                   0   |
| F1        | after_file_write    |       50 | DUP         | ok          |           0 |       75   |                    75   |                   0   |
| F1        | after_wm_write      |       50 | ok          | ok          |           0 |        0   |                     0   |                   0   |
| F2        | after_extract       |       50 | ok          | ok          |           0 |        0   |                     0   |                   0   |
| F2        | mid_file_write      |       50 | ok          | ok          |           0 |        0   |                    37.2 |                   0   |
| F2        | after_file_write    |       50 | ok          | ok          |           0 |        0   |                    75   |                   0   |
| F2        | after_manifest_tmp  |       50 | ok          | ok          |           0 |        0   |                    75   |                   0   |
| F2        | after_commit        |       50 | ok          | ok          |           0 |        0   |                     0   |                   0   |
| F3        | after_extract       |       50 | ok          | ok          |           0 |        0   |                     0   |                   0   |
| F3        | mid_file_write      |       50 | ok          | ok          |           0 |        0   |                    37.2 |                   0   |
| F3        | after_file_write    |       50 | ok          | ok          |           0 |        0   |                    75   |                   0   |
| F3        | mid_manifest_write  |       50 | CORRUPT     | unreadable  |           0 |        0   |                     0   |                   0   |
| F3        | after_commit        |       50 | ok          | ok          |           0 |        0   |                     0   |                   0   |

## E1: per-pattern

| pattern   |   trials |   crash_points |   final_bad |   transient_bad |   unsafe_points_final |   unsafe_points_transient |
|:----------|---------:|---------------:|------------:|----------------:|----------------------:|--------------------------:|
| A1        |      200 |              4 |          50 |               0 |                     1 |                         0 |
| A2        |      200 |              4 |         100 |               0 |                     2 |                         0 |
| A3        |      200 |              4 |           0 |               0 |                     0 |                         0 |
| A4        |      150 |              3 |           0 |               0 |                     0 |                         0 |
| M1        |      200 |              4 |           0 |               0 |                     0 |                         0 |
| M2        |      150 |              3 |           0 |               0 |                     0 |                         0 |
| P1        |      250 |              5 |           0 |              98 |                     0 |                         2 |
| P2        |      150 |              3 |           0 |               0 |                     0 |                         0 |
| F1        |      200 |              4 |         100 |              44 |                     2 |                         1 |
| F2        |      250 |              5 |           0 |               0 |                     0 |                         0 |
| F3        |      250 |              5 |          50 |              50 |                     1 |                         1 |

## E2: predicate x lag (subset)

| pattern   | pred          |   p_lag |   loss_pct |   loss_max |   dup_pct |   read_amp |   runs_with_loss |   n |
|:----------|:--------------|--------:|-----------:|-----------:|----------:|-----------:|-----------------:|----:|
| A4        | gt            |    0    |      0     |      0     |     0     |      1     |                0 |  10 |
| A4        | gt            |    0.05 |      3.3   |      5.085 |     0     |      0.967 |               10 |  10 |
| A4        | gt            |    0.2  |     13.553 |     16.123 |     0     |      0.864 |               10 |  10 |
| A4        | gte           |    0    |      0     |      0     |    11.239 |      1.112 |                0 |  10 |
| A4        | gte           |    0.05 |      3.064 |      4.79  |    10.86  |      1.078 |               10 |  10 |
| A4        | gte           |    0.2  |     12.029 |     14.954 |     9.368 |      0.973 |               10 |  10 |
| A4        | lookback L=2  |    0    |      0     |      0     |    20.919 |      1.209 |                0 |  10 |
| A4        | lookback L=2  |    0.05 |      2.647 |      4.348 |    20.775 |      1.181 |               10 |  10 |
| A4        | lookback L=2  |    0.2  |     10.928 |     14.031 |    18.639 |      1.077 |               10 |  10 |
| A4        | lookback L=5  |    0    |      0     |      0     |    52.836 |      1.528 |                0 |  10 |
| A4        | lookback L=5  |    0.05 |      1.757 |      3.021 |    51.199 |      1.494 |               10 |  10 |
| A4        | lookback L=5  |    0.2  |      6.803 |      9.354 |    45.85  |      1.39  |               10 |  10 |
| A4        | lookback L=10 |    0    |      0     |      0     |   105.915 |      2.059 |                0 |  10 |
| A4        | lookback L=10 |    0.05 |      0.357 |      0.679 |   102.531 |      2.022 |                9 |  10 |
| A4        | lookback L=10 |    0.2  |      1.658 |      2.4   |    92.189 |      1.905 |               10 |  10 |
| A4        | lookback L=15 |    0    |      0     |      0     |   155.019 |      2.55  |                0 |  10 |
| A4        | lookback L=15 |    0.05 |      0     |      0     |   152.075 |      2.521 |                0 |  10 |
| A4        | lookback L=15 |    0.2  |      0     |      0     |   141.769 |      2.418 |                0 |  10 |
| A4        | lookback L=20 |    0    |      0     |      0     |   205.642 |      3.056 |                0 |  10 |
| A4        | lookback L=20 |    0.05 |      0     |      0     |   202.049 |      3.02  |                0 |  10 |
| A4        | lookback L=20 |    0.2  |      0     |      0     |   190.099 |      2.901 |                0 |  10 |
| M2        | gt            |    0    |      0     |      0     |     0     |      1     |                0 |  10 |
| M2        | gt            |    0.05 |      3.3   |      5.085 |     0     |      0.967 |               10 |  10 |
| M2        | gt            |    0.2  |     13.553 |     16.123 |     0     |      0.864 |               10 |  10 |
| M2        | gte           |    0    |      0     |      0     |     0     |      1.112 |                0 |  10 |
| M2        | gte           |    0.05 |      3.064 |      4.79  |     0     |      1.078 |               10 |  10 |
| M2        | gte           |    0.2  |     12.029 |     14.954 |     0     |      0.973 |               10 |  10 |
| M2        | lookback L=2  |    0    |      0     |      0     |     0     |      1.209 |                0 |  10 |
| M2        | lookback L=2  |    0.05 |      2.647 |      4.348 |     0     |      1.181 |               10 |  10 |
| M2        | lookback L=2  |    0.2  |     10.928 |     14.031 |     0     |      1.077 |               10 |  10 |
| M2        | lookback L=5  |    0    |      0     |      0     |     0     |      1.528 |                0 |  10 |
| M2        | lookback L=5  |    0.05 |      1.757 |      3.021 |     0     |      1.494 |               10 |  10 |
| M2        | lookback L=5  |    0.2  |      6.803 |      9.354 |     0     |      1.39  |               10 |  10 |
| M2        | lookback L=10 |    0    |      0     |      0     |     0     |      2.059 |                0 |  10 |
| M2        | lookback L=10 |    0.05 |      0.357 |      0.679 |     0     |      2.022 |                9 |  10 |
| M2        | lookback L=10 |    0.2  |      1.658 |      2.4   |     0     |      1.905 |               10 |  10 |
| M2        | lookback L=15 |    0    |      0     |      0     |     0     |      2.55  |                0 |  10 |
| M2        | lookback L=15 |    0.05 |      0     |      0     |     0     |      2.521 |                0 |  10 |
| M2        | lookback L=15 |    0.2  |      0     |      0     |     0     |      2.418 |                0 |  10 |
| M2        | lookback L=20 |    0    |      0     |      0     |     0     |      3.056 |                0 |  10 |
| M2        | lookback L=20 |    0.05 |      0     |      0     |     0     |      3.02  |                0 |  10 |
| M2        | lookback L=20 |    0.2  |      0     |      0     |     0     |      2.901 |                0 |  10 |
| P2        | gt            |    0    |      0     |      0     |     0     |      2.097 |                0 |  10 |
| P2        | gt            |    0.05 |      3.084 |      4.79  |     0     |      2.037 |               10 |  10 |
| P2        | gt            |    0.2  |     12.172 |     15.138 |     0     |      1.823 |               10 |  10 |
| P2        | gte           |    0    |      0     |      0     |     0     |      2.282 |                0 |  10 |
| P2        | gte           |    0.05 |      2.776 |      4.79  |     0     |      2.236 |               10 |  10 |
| P2        | gte           |    0.2  |     11.251 |     14.954 |     0     |      2.011 |               10 |  10 |
| P2        | lookback L=2  |    0    |      0     |      0     |     0     |      3.317 |                0 |  10 |
| P2        | lookback L=2  |    0.05 |      0.418 |      0.907 |     0     |      3.237 |               10 |  10 |
| P2        | lookback L=2  |    0.2  |      1.596 |      2.954 |     0     |      3.024 |               10 |  10 |
| P2        | lookback L=5  |    0    |      0     |      0     |     0     |      3.684 |                0 |  10 |
| P2        | lookback L=5  |    0.05 |      0.255 |      0.679 |     0     |      3.609 |                8 |  10 |
| P2        | lookback L=5  |    0.2  |      1.058 |      2.031 |     0     |      3.389 |               10 |  10 |
| P2        | lookback L=10 |    0    |      0     |      0     |     0     |      4.217 |                0 |  10 |
| P2        | lookback L=10 |    0.05 |      0.255 |      0.679 |     0     |      4.142 |                8 |  10 |
| P2        | lookback L=10 |    0.2  |      1.058 |      2.031 |     0     |      3.914 |               10 |  10 |
| P2        | lookback L=15 |    0    |      0     |      0     |     0     |      5.696 |                0 |  10 |
| P2        | lookback L=15 |    0.05 |      0     |      0     |     0     |      5.629 |                0 |  10 |
| P2        | lookback L=15 |    0.2  |      0     |      0     |     0     |      5.409 |                0 |  10 |
| P2        | lookback L=20 |    0    |      0     |      0     |     0     |      6.207 |                0 |  10 |
| P2        | lookback L=20 |    0.05 |      0     |      0     |     0     |      6.135 |                0 |  10 |
| P2        | lookback L=20 |    0.2  |      0     |      0     |     0     |      5.903 |                0 |  10 |
| F2        | gt            |    0    |      0     |      0     |     0     |      1     |                0 |  10 |
| F2        | gt            |    0.05 |      3.3   |      5.085 |     0     |      0.967 |               10 |  10 |
| F2        | gt            |    0.2  |     13.553 |     16.123 |     0     |      0.864 |               10 |  10 |
| F2        | gte           |    0    |      0     |      0     |    11.239 |      1.112 |                0 |  10 |
| F2        | gte           |    0.05 |      3.064 |      4.79  |    10.86  |      1.078 |               10 |  10 |
| F2        | gte           |    0.2  |     12.029 |     14.954 |     9.368 |      0.973 |               10 |  10 |
| F2        | lookback L=2  |    0    |      0     |      0     |    20.919 |      1.209 |                0 |  10 |
| F2        | lookback L=2  |    0.05 |      2.647 |      4.348 |    20.775 |      1.181 |               10 |  10 |
| F2        | lookback L=2  |    0.2  |     10.928 |     14.031 |    18.639 |      1.077 |               10 |  10 |
| F2        | lookback L=5  |    0    |      0     |      0     |    52.836 |      1.528 |                0 |  10 |
| F2        | lookback L=5  |    0.05 |      1.757 |      3.021 |    51.199 |      1.494 |               10 |  10 |
| F2        | lookback L=5  |    0.2  |      6.803 |      9.354 |    45.85  |      1.39  |               10 |  10 |
| F2        | lookback L=10 |    0    |      0     |      0     |   105.915 |      2.059 |                0 |  10 |
| F2        | lookback L=10 |    0.05 |      0.357 |      0.679 |   102.531 |      2.022 |                9 |  10 |
| F2        | lookback L=10 |    0.2  |      1.658 |      2.4   |    92.189 |      1.905 |               10 |  10 |
| F2        | lookback L=15 |    0    |      0     |      0     |   155.019 |      2.55  |                0 |  10 |
| F2        | lookback L=15 |    0.05 |      0     |      0     |   152.075 |      2.521 |                0 |  10 |
| F2        | lookback L=15 |    0.2  |      0     |      0     |   141.769 |      2.418 |                0 |  10 |
| F2        | lookback L=20 |    0    |      0     |      0     |   205.642 |      3.056 |                0 |  10 |
| F2        | lookback L=20 |    0.05 |      0     |      0     |   202.049 |      3.02  |                0 |  10 |
| F2        | lookback L=20 |    0.2  |      0     |      0     |   190.099 |      2.901 |                0 |  10 |

## E3: crashes + 5% late commits, per configuration

| config             |   trials |   trials_with_loss |   trials_with_dup |   trials_correct |
|:-------------------|---------:|-------------------:|------------------:|-----------------:|
| A4 / gt            |       40 |                 40 |                 0 |                0 |
| A4 / lookback L=15 |       40 |                  0 |                40 |                0 |
| M2 / gt            |       40 |                 40 |                 0 |                0 |
| M2 / lookback L=15 |       40 |                  0 |                 0 |               40 |
| M1 / lookback L=15 |       50 |                  0 |                 0 |               50 |
| A1 / lookback L=15 |       50 |                  0 |                50 |                0 |
| P2 / gt            |       40 |                 40 |                 0 |                0 |
| P2 / lookback L=15 |       40 |                  0 |                 0 |               40 |

## E4: SIGKILL fuzzing (2200 runs)

| pattern   |   trials |   killed |   final_bad |   lost |   dup |   corrupt |   stuck |   transient_regress |   transient_unreadable |   p_final_bad_given_kill |
|:----------|---------:|---------:|------------:|-------:|------:|----------:|--------:|--------------------:|-----------------------:|-------------------------:|
| A1        |      200 |      177 |          39 |      0 |    39 |         0 |       0 |                   0 |                      0 |                    0.22  |
| A2        |      200 |      193 |          76 |     76 |     0 |         0 |       0 |                   0 |                      0 |                    0.394 |
| A3        |      200 |      175 |           0 |      0 |     0 |         0 |       0 |                   0 |                      0 |                    0     |
| A4        |      200 |      169 |           0 |      0 |     0 |         0 |       0 |                   0 |                      0 |                    0     |
| M1        |      200 |      179 |           0 |      0 |     0 |         0 |       0 |                   0 |                      0 |                    0     |
| M2        |      200 |      166 |           0 |      0 |     0 |         0 |       0 |                   0 |                      0 |                    0     |
| P1        |      200 |      187 |           0 |      0 |     0 |         0 |       0 |                  61 |                      0 |                    0     |
| P2        |      200 |      187 |           0 |      0 |     0 |         0 |       0 |                   0 |                      0 |                    0     |
| F1        |      200 |      188 |          46 |      0 |    46 |         0 |       0 |                   0 |                      0 |                    0.245 |
| F2        |      200 |      177 |           0 |      0 |     0 |         0 |       0 |                   0 |                      0 |                    0     |
| F3        |      200 |      171 |           1 |      0 |     0 |         1 |       1 |                   0 |                      1 |                    0.006 |

## E4 vs E1
Killed runs: 1969. Runs where E1 predicts ok and the kill was ok, or E1 predicts an anomaly and one occurred: 1375/1440

pattern  last_cp            final_ok
A1       after_data_commit  True         2
         mid_data_txn       False        6
A2       after_extract      False        7
         mid_data_txn       True         4
F1       after_extract      False       33
         after_file_write   True        12
F3       after_file_write   False        1