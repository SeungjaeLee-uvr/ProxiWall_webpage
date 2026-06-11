# User event log quantitative analysis

## Design and interpretation

- 36 sessions: 6 participants x 6 sessions.
- Conditions: Ours and Baseline, 3 sessions per participant per condition.
- Participants were inferred from chronological blocks of six sessions.
- `space_pressed` is treated as the answer timestamp.
- Every `space_pressed` is a correct answer, so selection accuracy is correct space presses / all space presses.
- Candidate-selected equality is reported separately as selection alignment/consistency.

## Participant-level condition means

| condition   |   active_duration_s |   first_answer_s |   between_answers_s |   candidate_changes |   pose_losses |   alignment_rate |   selection_accuracy |
|:------------|--------------------:|-----------------:|--------------------:|--------------------:|--------------:|-----------------:|---------------------:|
| Baseline    |              87.613 |           37.682 |              46.366 |              13.278 |         4.611 |            1     |                    1 |
| Ours        |              54.739 |           24.785 |              24.819 |              21.389 |         2.444 |            0.667 |                    1 |

## Paired condition tests

| metric                              |   n_pairs |   Ours_mean |   Baseline_mean |   mean_difference_Ours_minus_Baseline |   difference_95ci_low |   difference_95ci_high |   cohen_dz |   paired_t |   paired_t_p |   wilcoxon_w |   wilcoxon_p |
|:------------------------------------|----------:|------------:|----------------:|--------------------------------------:|----------------------:|-----------------------:|-----------:|-----------:|-------------:|-------------:|-------------:|
| active_duration_s                   |         6 |     54.7395 |         87.6133 |                              -32.8738 |              -62.0194 |                -3.7282 |    -1.1837 |    -2.8994 |       0.0338 |          0   |       0.0312 |
| task_completion_time_s              |         6 |     24.8022 |         42.0238 |                              -17.2215 |              -31.3987 |                -3.0444 |    -1.2748 |    -3.1226 |       0.0262 |          0   |       0.0312 |
| time_to_first_answer_s              |         6 |     24.785  |         37.6815 |                              -12.8965 |              -25.5134 |                -0.2797 |    -1.0727 |    -2.6276 |       0.0467 |          0   |       0.0312 |
| time_to_second_answer_s             |         6 |     24.8194 |         46.366  |                              -21.5466 |              -49.482  |                 6.3889 |    -0.8094 |    -1.9827 |       0.1042 |          0   |       0.0312 |
| candidate_changes                   |         6 |     21.3889 |         13.2778 |                                8.1111 |               -0.2483 |                16.4706 |     1.0183 |     2.4942 |       0.0549 |          2   |       0.0938 |
| mode_changes                        |         6 |     12.2778 |         19.7222 |                               -7.4444 |              -19.8924 |                 5.0035 |    -0.6276 |    -1.5373 |       0.1848 |          3   |       0.1562 |
| forward_mode_transitions            |         6 |      8.6667 |         10.8333 |                               -2.1667 |               -8.6197 |                 4.2864 |    -0.3524 |    -0.8631 |       0.4275 |          7   |       0.5625 |
| backward_mode_transitions           |         6 |      3.6111 |          8.8889 |                               -5.2778 |              -11.3907 |                 0.8351 |    -0.9061 |    -2.2194 |       0.0772 |          0   |       0.0312 |
| detail_entries                      |         6 |      3.2778 |          6.3889 |                               -3.1111 |               -8.1448 |                 1.9226 |    -0.6486 |    -1.5888 |       0.173  |          4   |       0.2188 |
| pose_losses                         |         6 |      2.4444 |          4.6111 |                               -2.1667 |               -4.0276 |                -0.3057 |    -1.2219 |    -2.9929 |       0.0303 |          0   |       0.125  |
| path_distance_position_depth        |         6 |      3.6803 |          3.7388 |                               -0.0584 |               -1.3692 |                 1.2523 |    -0.0468 |    -0.1146 |       0.9132 |          9   |       0.8438 |
| correct_alignment_rate              |         6 |      0.6667 |          1      |                               -0.3333 |               -0.444  |                -0.2227 |    -3.1623 |    -7.746  |       0.0006 |          0   |       0.0312 |
| selection_accuracy                  |         6 |      1      |          1      |                                0      |                0      |                 0      |     0      |     0      |       1      |          0   |       1      |
| wrong_candidate_visit_events_proxy  |         6 |      7.1111 |          4.8167 |                                2.2944 |               -1.6487 |                 6.2376 |     0.6106 |     1.4958 |       0.195  |          4   |       0.2188 |
| wrong_unique_candidates_proxy       |         6 |      3.1389 |          2.8889 |                                0.25   |               -1.0389 |                 1.5389 |     0.2036 |     0.4986 |       0.6392 |          7   |       0.5625 |
| wrong_detail_visits_proxy           |         6 |      0.5    |          1.8944 |                               -1.3944 |               -3.9464 |                 1.1575 |    -0.5734 |    -1.4046 |       0.2191 |          4.5 |       0.25   |
| wrong_selection_confirmations_proxy |         6 |      0.5    |          1.8944 |                               -1.3944 |               -3.9464 |                 1.1575 |    -0.5734 |    -1.4046 |       0.2191 |          4.5 |       0.25   |
| wrong_touches_rule                  |         6 |      3.6111 |         19.2222 |                              -15.6111 |              -27.7681 |                -3.4541 |    -1.3476 |    -3.301  |       0.0215 |          0   |       0.0312 |
| wrong_touch_rate_rule               |         6 |      0.5101 |          0.8575 |                               -0.3474 |               -0.5392 |                -0.1556 |    -1.9004 |    -4.6549 |       0.0056 |          0   |       0.0312 |
| wrong_selection_touches_rule        |         6 |      1.2778 |          4.3889 |                               -3.1111 |               -8.1448 |                 1.9226 |    -0.6486 |    -1.5888 |       0.173  |          4   |       0.2188 |

## Data quality

- Parsed 3,068 event rows.
- Repaired 4 malformed `space_pressed` rows in the first two logs.
- Sessions with exactly two `space_pressed` events: 36 / 36.

See the CSV files for all session-, answer-, event-, mode-, and participant-level metrics.