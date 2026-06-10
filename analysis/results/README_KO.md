# 사용자 이벤트 로그 정량 분석 요약

## 실험 구조와 전처리

- 총 36개 세션, 3,068개 이벤트, `space_pressed` 72회
- 시간순 6개 세션을 한 사용자로 묶어 사용자 6명을 추론
- 각 사용자: `MoveDistance` 3회 + `ScreenTouch` 3회
- 사용자 1·3·5는 MoveDistance 먼저, 사용자 2·4·6은 ScreenTouch 먼저
- 초기 2개 로그의 구분자 오류가 있는 `space_pressed` 4행을 읽기 단계에서 복구
- 모든 세션에 `space_pressed`가 정확히 2회 존재

`space_pressed`는 사용자가 정답을 말한 시점이며 모든 `space_pressed`는 정답으로 판정했다. 따라서 Selection Accuracy는 `정답 space_pressed 수 / 전체 space_pressed 수`이다. `candidate_index == selected_index`는 정확도와 분리하여, 답을 말한 순간 화면 후보와 확정 선택의 일치 여부를 나타내는 UI 선택 일치도 지표로 사용한다.

## 산출 지표

- Task Completion Time: 활성 시작~첫 응답, 첫 응답~두 번째 응답을 각각 한 task로 계산
- 시간: 전체/활성 세션 시간, 첫 응답까지 시간, 응답 사이 시간, 모드별 체류 시간
- 정확도: 정답 `space_pressed` 수 / 전체 `space_pressed` 수
- 응답 상태: 유효 selected 응답 수, candidate-selected UI 선택 일치 수와 비율
- 탐색: 후보 변경 수, 고유 후보 수, 탐색 방향 반전 수
- Wrong Touch: 한 `touch_started`와 다음 `touch_started` 사이에 `space_pressed`가 없으면 앞선 touch를 wrong으로 판정
- Wrong Selection Touch: 같은 규칙을 유물 선택 이벤트인 `selection_confirmed`에 적용
- Wrong Visit proxy: 최종 응답 유물을 목표로 간주한 오답 후보 방문과 오답 Detail 진입
- 상세 보기: Detail 진입/이탈 수, selection confirmation 수
- 모드 전환: 전체/forward/backward 전환 수, 실제 전환 경로, 전환 직전 3초의 후보 변경·이동·depth 변화
- 트래킹: pose loss 수와 누적 pose loss 시간
- 터치: touch start 수와 누적 터치 시간
- 이동: position-depth 경로 길이, position/depth 범위, 조건·모드별 히트맵, 세션 궤적
- 밀도: 이벤트 수와 분당 이벤트 수
- 응답 구간별: 각 응답 전 후보 변경, 고유 후보, 상세 진입, pose loss, 경로 길이
- 통계: 사용자별 컨디션 평균을 이용한 paired t-test, Wilcoxon test, Cohen's dz, 평균차 95% CI

## 핵심 결과

| 지표 | MoveDistance | ScreenTouch | 해석 |
|---|---:|---:|---|
| Selection Accuracy | 100% (36/36) | 100% (36/36) | 모든 `space_pressed`가 정답, 조건 차이 없음 |
| 평균 Task Completion Time | 24.80초 | 42.02초 | MoveDistance가 평균 17.22초 빠름 |
| 평균 활성 시간 | 54.74초 | 87.61초 | MoveDistance가 평균 32.87초 짧음 |
| 첫 응답까지 시간 | 24.79초 | 37.68초 | MoveDistance가 평균 12.90초 빠름 |
| 두 응답 사이 시간 | 24.82초 | 46.37초 | MoveDistance가 평균 21.55초 빠름 |
| 후보 변경 수 | 21.39회 | 13.28회 | MoveDistance에서 탐색 후보 전환이 많음 |
| 탐색 방향 반전 수 | 8.22회 | 3.50회 | MoveDistance에서 왕복 탐색이 많음 |
| Detail 진입 수 | 3.28회 | 6.39회 | ScreenTouch에서 상세 진입이 많음 |
| Pose loss 수 | 2.44회 | 4.61회 | ScreenTouch에서 발생 횟수가 많음 |
| position-depth 경로 길이 | 3.68 | 3.74 | 컨디션 차이가 거의 없음 |
| 모드 전환 수 | 12.28회 | 19.72회 | ScreenTouch에서 전환이 더 많음 |
| backward 모드 전환 수 | 3.61회 | 8.89회 | ScreenTouch에서 이전 단계 복귀가 더 많음 |
| Wrong candidate visit event proxy/task | 7.11회 | 4.83회 | MoveDistance에서 후보 스캔이 더 많음 |
| Wrong Detail/confirmation proxy/task | 0.50회 | 1.94회 | ScreenTouch에서 목표 외 상세 진입 proxy가 더 많음 |
| Wrong Touch/task | 1.69회 | 9.58회 | ScreenTouch에서 응답 없이 이어진 터치가 많음 |
| Wrong Touch/session | 3.61회 | 19.22회 | ScreenTouch에서 평균 15.61회 많음 |
| Wrong Touch rate | 51.0% | 85.8% | ScreenTouch의 wrong-touch 비율이 높음 |
| Wrong Selection Touch/session | 1.28회 | 4.39회 | 유물 선택 이벤트만 보아도 ScreenTouch가 많음 |

사용자별 paired t-test에서 `MoveDistance`는 Task Completion Time(`p=.0262`), 활성 시간(`p=.0338`), 첫 응답 시간(`p=.0467`)이 유의하게 짧았다. Pose loss 발생 횟수도 더 적었다(`p=.0303`). 후보 변경 수 차이는 효과크기는 크지만(`dz=1.02`) 표본 6명에서 `p=.0549`로 경계 수준이다.

모드 경로는 시스템 설계 차이를 그대로 보여준다. MoveDistance는 `Browsing → TouchConfirmed → Detail` 경로를 사용하고, ScreenTouch는 `Browsing → Detail`로 직접 진입한다. 따라서 단순 총 전환 수만으로 자연스러움을 판단하면 안 되며, backward 전환과 전환 직전 행동을 함께 보는 편이 적절하다.

전환 직전 3초 동안 MoveDistance는 ScreenTouch보다 후보 변경과 position-depth 경로 이동이 많았다. 특히 MoveDistance의 forward 전환 직전 depth 변화가 양수로 나타나, 거리 기반 Semantic Zoom의 “전진 후 상세 단계 진입” 패턴을 Discussion 자료로 사용할 수 있다.

정의된 Wrong Touch 규칙에서 총 `touch_started` 483회 중 MoveDistance는 65회, ScreenTouch는 346회가 wrong으로 분류되었다. 세션별 사용자 paired test에서도 MoveDistance의 Wrong Touch 수가 유의하게 적었다(`p=.0215`, `dz=-1.35`). 터치 수 차이의 영향을 일부 통제한 Wrong Touch rate도 MoveDistance가 낮았다(`p=.0056`, `dz=-1.90`).

두 조건 모두 `space_pressed` 36회가 전부 정답이므로 Selection Accuracy는 100%이다. 즉, Accuracy에는 ceiling effect가 있어 조건 차이를 설명하지 못하며 Completion Time과 Wrong Touch가 핵심 성능 차이를 보여준다.

별도 UI 상태 지표로, `MoveDistance`의 유효 selected 응답 35개 중 24개가 candidate와 일치했고 `ScreenTouch`는 유효 selected 응답 32개 모두 일치했다. 이는 정답률이 아니라 사용자가 정답을 말한 순간 후보와 확정 선택이 같은지를 나타낸다.

## 해석 시 주의

- 참가자가 6명뿐이므로 p-value보다 사용자별 paired trajectory와 효과크기를 함께 봐야 한다.
- 모든 `space_pressed`를 정답으로 판정하므로 Accuracy는 계산 가능하지만, 두 조건 모두 100%인 ceiling effect가 있다.
- Wrong Touch는 사용자 정의 규칙에 따라 계산되므로 실제 목표 유물을 건드렸는지와는 독립적이다. 화면 이동·상세 종료용 터치도 `touch_started`라면 wrong으로 포함된다.
- 실제 유물 선택만 보고 싶을 때는 `wrong_selection_touches_rule`을 사용한다.
- Wrong Visit proxy는 `space_pressed` 시점의 selected/candidate를 목표로 간주하므로 실제 목표 유물이 잘못 선택된 경우 왜곡된다.
- `space_pressed` 시점만으로는 발화 내용의 의미적 정오를 판별할 수 없다.
- 위치는 연속 프레임 샘플이 아니라 이벤트 발생 시점 샘플이므로, 히트맵 밀도는 실제 체류시간과 정확히 같지 않다.
- `position`과 `depth`는 camera-space 정규화 좌표이며 실제 이동 거리(m)가 아니다.
- 사용자 ID는 로그에 직접 저장되지 않아 시간순 블록으로 추론했다.
- 세션 순서 그래프에서 두 컨디션 모두 큰 개인차가 보이며, 명확한 단조 학습 효과는 확인되지 않는다.

## 요청 지표 완료 여부

| 요청 지표 | 상태 | 현재 산출물 |
|---|---|---|
| Task Completion Time | 완료 | task별/세션별 시간 및 paired test |
| Selection Accuracy | 완료 | 모든 `space_pressed`를 정답으로 판정하여 조건별 100% |
| Mode Transition Count | 완료 | 전체, forward/backward, 경로별 전환 |
| Mode-wise Dwell Time | 완료 | 조건·세션별 Overview/Browsing/TouchConfirmed/Detail 체류 |
| Wrong Touches | 완료 | 연속 touch 사이 `space_pressed` 존재 여부로 판정 |
| Wrong Candidate Visits | proxy 완료 | 최종 응답 유물 기준 후보/Detail 오답 방문 |
| 이동 궤적/히트맵 | 완료 | 조건·모드별 히트맵과 세션 궤적 |
| 모드 전환 직전 행동 | 완료 | 전환 직전 3초 후보 변경, 경로, position/depth 변화 |

향후 로그에는 `participant_id`, `task_id`, `target_artifact_id`, `spoken_answer`, 그리고 고정 주기의 위치 샘플을 기록하는 것이 좋다. 현재처럼 모든 제출이 정답인 실험에서는 Accuracy가 변별력을 갖지 못하므로 오류가 발생할 수 있는 과제 설계나 난이도 조건도 고려할 수 있다.

## 결과 파일

- `session_metrics.csv`: 세션별 전체 지표
- `answer_metrics.csv`: 72개 응답 및 응답 전 구간 지표
- `participant_condition_summary.csv`: 사용자별 컨디션 평균
- `condition_summary.csv`: 컨디션별 기술통계
- `paired_tests.csv`: paired 통계검정
- `event_counts.csv`: 세션별 이벤트 종류별 빈도
- `mode_durations.csv`: 세션별 모드 체류 시간
- `mode_transitions.csv`: 전환 경로와 전환 직전 3초 행동
- `position_observations.csv`: 이벤트 시점 위치 관측
- `task_and_wrong_visit_summary.csv`: task 시간과 Wrong Visit proxy 요약
- `wrong_touch_classification.csv`: 모든 touch의 wrong/answered 판정
- `data_quality.csv`: 파일별 파싱 및 품질 점검
- `figures/`: Python으로 생성한 그래프
