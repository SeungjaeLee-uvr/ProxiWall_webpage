#!/usr/bin/env python3
"""Analyze the 6-participant x 6-session user event log experiment."""

from __future__ import annotations

import csv
import math
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "user_events_log"
OUT_DIR = ROOT / "analysis" / "results"
FIG_DIR = OUT_DIR / "figures"
CONDITIONS = ["MoveDistance", "ScreenTouch"]
MODE_ORDER = ["Overview", "Browsing", "TouchConfirmed", "Detail"]
MODE_RANK = {"Overview": 0, "Browsing": 1, "TouchConfirmed": 2, "Detail": 3}


def parse_malformed_space_row(line: str) -> list[str] | None:
    """Recover early space_pressed rows whose delimiters were partly spaces."""
    pattern = re.compile(
        r"^(\S+)\s+(\S+)\s+(\S+)\s+(space_pressed)\t"
        r"([^\t]*)\t([^\t]*)\t([^\t]*)\s+(\S+)\t(\S+)\s+(.*)$"
    )
    match = pattern.match(line.rstrip("\r\n"))
    return list(match.groups()) if match else None


def read_log(path: Path) -> tuple[pd.DataFrame, int]:
    rows: list[list[str]] = []
    repaired = 0
    with path.open(encoding="utf-8", newline="") as handle:
        header = next(csv.reader([handle.readline().rstrip("\r\n")], delimiter="\t"))
        for line in handle:
            row = next(csv.reader([line.rstrip("\r\n")], delimiter="\t"))
            if len(row) != len(header):
                row = parse_malformed_space_row(line) or row
                repaired += int(len(row) == len(header))
            if len(row) != len(header):
                raise ValueError(f"Cannot parse {path.name}: expected {len(header)} columns, got {len(row)}")
            rows.append(row)

    frame = pd.DataFrame(rows, columns=header)
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True)
    frame["timestamp_local"] = pd.to_datetime(frame["timestamp_local"], utc=True)
    for col in ["candidate_index", "selected_index", "position", "depth"]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    frame["source_file"] = path.name
    return frame, repaired


def paired_test(table: pd.DataFrame, metric: str) -> dict[str, float | str]:
    pivot = table.pivot(index="participant", columns="condition", values=metric).dropna()
    move = pivot["MoveDistance"].to_numpy()
    touch = pivot["ScreenTouch"].to_numpy()
    diff = move - touch
    if np.allclose(diff, 0):
        return {
            "metric": metric,
            "n_pairs": len(diff),
            "MoveDistance_mean": move.mean(),
            "ScreenTouch_mean": touch.mean(),
            "mean_difference_Move_minus_Touch": 0.0,
            "difference_95ci_low": 0.0,
            "difference_95ci_high": 0.0,
            "cohen_dz": 0.0,
            "paired_t": 0.0,
            "paired_t_p": 1.0,
            "wilcoxon_w": 0.0,
            "wilcoxon_p": 1.0,
        }
    t_result = stats.ttest_rel(move, touch)
    try:
        w_result = stats.wilcoxon(move, touch)
        w_stat, w_p = float(w_result.statistic), float(w_result.pvalue)
    except ValueError:
        w_stat, w_p = math.nan, math.nan
    return {
        "metric": metric,
        "n_pairs": len(diff),
        "MoveDistance_mean": move.mean(),
        "ScreenTouch_mean": touch.mean(),
        "mean_difference_Move_minus_Touch": diff.mean(),
        "difference_95ci_low": stats.t.interval(0.95, len(diff) - 1, loc=diff.mean(), scale=stats.sem(diff))[0],
        "difference_95ci_high": stats.t.interval(0.95, len(diff) - 1, loc=diff.mean(), scale=stats.sem(diff))[1],
        "cohen_dz": diff.mean() / diff.std(ddof=1) if diff.std(ddof=1) else math.nan,
        "paired_t": float(t_result.statistic),
        "paired_t_p": float(t_result.pvalue),
        "wilcoxon_w": w_stat,
        "wilcoxon_p": w_p,
    }


def event_pair_duration(frame: pd.DataFrame, start_event: str, end_event: str) -> float:
    start = None
    total = 0.0
    for row in frame.itertuples():
        if row.event == start_event and start is None:
            start = row.timestamp_utc
        elif row.event == end_event and start is not None:
            total += (row.timestamp_utc - start).total_seconds()
            start = None
    if start is not None:
        total += (frame["timestamp_utc"].iloc[-1] - start).total_seconds()
    return total


def detail_index(row: pd.Series) -> float:
    match = re.search(r"artifact_index=(\d+)", str(row["details"]))
    return float(match.group(1)) if match else row["selected_index"]


def classify_touches(frame: pd.DataFrame, touch_event: str) -> pd.DataFrame:
    """A touch is wrong when no space_pressed occurs before the next touch."""
    relevant = frame[frame["event"].isin([touch_event, "space_pressed"])].copy()
    touches = []
    for position, (_, row) in enumerate(relevant.iterrows()):
        if row["event"] != touch_event:
            continue
        later = relevant.iloc[position + 1 :]
        next_relevant = later.iloc[0]["event"] if len(later) else None
        touches.append(
            {
                "timestamp_utc": row["timestamp_utc"],
                "event": touch_event,
                "mode": row["mode"],
                "candidate_index": row["candidate_index"],
                "selected_index": row["selected_index"],
                "position": row["position"],
                "depth": row["depth"],
                "wrong_touch": next_relevant != "space_pressed",
                "answered_touch": next_relevant == "space_pressed",
            }
        )
    return pd.DataFrame(touches)


def phase_metrics(
    frame: pd.DataFrame,
    answers: pd.DataFrame,
    active_start: pd.Timestamp,
    literal_touches: pd.DataFrame,
    selection_touches: pd.DataFrame,
) -> list[dict]:
    result = []
    previous = active_start
    for answer_no, (_, answer) in enumerate(answers.iterrows(), start=1):
        phase = frame[(frame["timestamp_utc"] >= previous) & (frame["timestamp_utc"] <= answer["timestamp_utc"])]
        candidate = phase.loc[phase["event"] == "candidate_changed", "candidate_index"].dropna()
        positions = phase[["position", "depth"]].dropna().to_numpy()
        path = np.sqrt(np.square(np.diff(positions, axis=0)).sum(axis=1)).sum() if len(positions) > 1 else 0
        target_proxy = answer["selected_index"] if pd.notna(answer["selected_index"]) else answer["candidate_index"]
        detail_visits = phase[phase["event"] == "detail_entered"].copy()
        detail_visits["visit_index"] = detail_visits.apply(detail_index, axis=1)
        confirmations = phase.loc[phase["event"] == "selection_confirmed", "selected_index"].dropna()
        phase_literal_touches = literal_touches[
            (literal_touches["timestamp_utc"] >= previous)
            & (literal_touches["timestamp_utc"] <= answer["timestamp_utc"])
        ]
        phase_selection_touches = selection_touches[
            (selection_touches["timestamp_utc"] >= previous)
            & (selection_touches["timestamp_utc"] <= answer["timestamp_utc"])
        ]
        result.append(
            {
                "answer_no": answer_no,
                "answer_latency_s": (answer["timestamp_utc"] - previous).total_seconds(),
                "correct_alignment": bool(
                    pd.notna(answer["candidate_index"])
                    and pd.notna(answer["selected_index"])
                    and answer["candidate_index"] == answer["selected_index"]
                ),
                "is_correct": True,
                "valid_selected_answer": bool(pd.notna(answer["selected_index"])),
                "candidate_index": answer["candidate_index"],
                "selected_index": answer["selected_index"],
                "position": answer["position"],
                "depth": answer["depth"],
                "candidate_changes_before_answer": len(candidate),
                "unique_candidates_before_answer": candidate.nunique(),
                "detail_entries_before_answer": int((phase["event"] == "detail_entered").sum()),
                "selection_confirmations_before_answer": int((phase["event"] == "selection_confirmed").sum()),
                "pose_losses_before_answer": int((phase["event"] == "pose_tracking_lost").sum()),
                "path_distance_before_answer": path,
                "target_proxy_index": target_proxy,
                "wrong_candidate_visit_events_proxy": int((candidate != target_proxy).sum()) if pd.notna(target_proxy) else math.nan,
                "wrong_unique_candidates_proxy": int(candidate[candidate != target_proxy].nunique()) if pd.notna(target_proxy) else math.nan,
                "wrong_detail_visits_proxy": int((detail_visits["visit_index"] != target_proxy).sum()) if pd.notna(target_proxy) else math.nan,
                "wrong_selection_confirmations_proxy": int((confirmations != target_proxy).sum()) if pd.notna(target_proxy) else math.nan,
                "wrong_touches_rule": int(phase_literal_touches["wrong_touch"].sum()),
                "answered_touches_rule": int(phase_literal_touches["answered_touch"].sum()),
                "wrong_selection_touches_rule": int(phase_selection_touches["wrong_touch"].sum()),
            }
        )
        previous = answer["timestamp_utc"]
    return result


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="notebook")

    loaded = []
    quality_rows = []
    for path in sorted(LOG_DIR.glob("*.tsv")):
        frame, repaired = read_log(path)
        loaded.append(frame)
        quality_rows.append(
            {
                "source_file": path.name,
                "rows": len(frame),
                "repaired_rows": repaired,
                "space_pressed_count": int((frame["event"] == "space_pressed").sum()),
                "session_start_count": int((frame["event"] == "session_start").sum()),
                "session_end_count": int((frame["event"] == "session_end").sum()),
            }
        )

    sessions = sorted(loaded, key=lambda x: x["timestamp_utc"].iloc[0])
    session_rows = []
    answer_rows = []
    event_rows = []
    mode_rows = []
    transition_rows = []
    position_rows = []
    touch_rows = []

    for global_index, frame in enumerate(sessions):
        participant = global_index // 6 + 1
        participant_session = global_index % 6 + 1
        condition = "MoveDistance" if frame["scene"].iloc[0] == "MoveNavScene" else "ScreenTouch"
        condition_session = (
            sum(
                1
                for previous in sessions[participant * 6 - 6 : global_index]
                if ("MoveDistance" if previous["scene"].iloc[0] == "MoveNavScene" else "ScreenTouch") == condition
            )
            + 1
        )
        order = "MoveFirst" if sessions[(participant - 1) * 6]["scene"].iloc[0] == "MoveNavScene" else "TouchFirst"
        start, end = frame["timestamp_utc"].iloc[[0, -1]]
        active_candidates = frame.loc[
            (frame["event"] == "mode_changed") & frame["details"].str.contains("to=Browsing", na=False),
            "timestamp_utc",
        ]
        active_start = active_candidates.iloc[0] if len(active_candidates) else start
        answers = frame[frame["event"] == "space_pressed"].copy()
        literal_touches = classify_touches(frame, "touch_started")
        selection_touches = classify_touches(frame, "selection_confirmed")
        valid_answers = answers["selected_index"].notna().sum()
        correct = (
            answers["selected_index"].notna()
            & answers["candidate_index"].notna()
            & answers["selected_index"].eq(answers["candidate_index"])
        ).sum()

        intervals = frame["timestamp_utc"].shift(-1).sub(frame["timestamp_utc"]).dt.total_seconds().fillna(0)
        positions = frame[["position", "depth"]].dropna().to_numpy()
        path_distance = np.sqrt(np.square(np.diff(positions, axis=0)).sum(axis=1)).sum()
        candidate_series = frame.loc[frame["event"] == "candidate_changed", "candidate_index"].dropna()
        candidate_diff = candidate_series.diff().dropna()
        reversals = int(((candidate_diff * candidate_diff.shift(1)) < 0).sum())
        transition_frame = frame[frame["event"] == "mode_changed"].copy()

        base = {
            "participant": participant,
            "participant_order": order,
            "participant_session": participant_session,
            "condition": condition,
            "condition_session": condition_session,
            "source_file": frame["source_file"].iloc[0],
        }
        metrics = {
            **base,
            "session_duration_s": (end - start).total_seconds(),
            "active_duration_s": (end - active_start).total_seconds(),
            "events": len(frame),
            "event_rate_per_min": len(frame) / ((end - active_start).total_seconds() / 60),
            "answer_count": len(answers),
            "correct_answer_count": len(answers),
            "selection_accuracy": 1.0 if len(answers) else math.nan,
            "valid_answer_count": int(valid_answers),
            "correct_alignment_count": int(correct),
            "correct_alignment_rate": correct / valid_answers if valid_answers else math.nan,
            "time_to_first_answer_s": (answers["timestamp_utc"].iloc[0] - active_start).total_seconds() if len(answers) else math.nan,
            "time_to_second_answer_s": (answers["timestamp_utc"].iloc[1] - answers["timestamp_utc"].iloc[0]).total_seconds() if len(answers) > 1 else math.nan,
            "candidate_changes": int((frame["event"] == "candidate_changed").sum()),
            "unique_candidates": int(candidate_series.nunique()),
            "candidate_reversals": reversals,
            "detail_entries": int((frame["event"] == "detail_entered").sum()),
            "detail_exits": int((frame["event"] == "detail_exited").sum()),
            "selection_confirmations": int((frame["event"] == "selection_confirmed").sum()),
            "mode_changes": int((frame["event"] == "mode_changed").sum()),
            "forward_mode_transitions": 0,
            "backward_mode_transitions": 0,
            "pose_losses": int((frame["event"] == "pose_tracking_lost").sum()),
            "pose_lost_duration_s": event_pair_duration(frame, "pose_tracking_lost", "pose_tracking_restored"),
            "touch_starts": int((frame["event"] == "touch_started").sum()),
            "touch_duration_s": event_pair_duration(frame, "touch_started", "touch_ended"),
            "wrong_touches_rule": int(literal_touches["wrong_touch"].sum()) if len(literal_touches) else 0,
            "answered_touches_rule": int(literal_touches["answered_touch"].sum()) if len(literal_touches) else 0,
            "wrong_touch_rate_rule": literal_touches["wrong_touch"].mean() if len(literal_touches) else math.nan,
            "wrong_selection_touches_rule": int(selection_touches["wrong_touch"].sum()) if len(selection_touches) else 0,
            "path_distance_position_depth": path_distance,
            "position_range": frame["position"].max() - frame["position"].min(),
            "depth_range": frame["depth"].max() - frame["depth"].min(),
        }
        session_rows.append(metrics)

        for event, count in frame["event"].value_counts().items():
            event_rows.append({**base, "event": event, "count": count})
        for mode in MODE_ORDER:
            mode_rows.append({**base, "mode": mode, "duration_s": intervals[frame["mode"] == mode].sum()})
        phase_result = phase_metrics(frame, answers, active_start, literal_touches, selection_touches)
        for answer_metric in phase_result:
            answer_rows.append({**base, **answer_metric})
        for touch_kind, touches in [("touch_started", literal_touches), ("selection_confirmed", selection_touches)]:
            for _, touch in touches.iterrows():
                touch_rows.append({**base, "touch_kind": touch_kind, **touch.to_dict()})

        for row_index, row in transition_frame.iterrows():
            match = re.search(r"from=([^;]+);\s*to=([^;]+)", str(row["details"]))
            if not match:
                continue
            from_mode, to_mode = match.groups()
            before = frame[
                (frame["timestamp_utc"] >= row["timestamp_utc"] - pd.Timedelta(seconds=3))
                & (frame["timestamp_utc"] < row["timestamp_utc"])
            ]
            before_positions = before[["position", "depth"]].dropna().to_numpy()
            pre_path = (
                np.sqrt(np.square(np.diff(before_positions, axis=0)).sum(axis=1)).sum()
                if len(before_positions) > 1 else 0
            )
            direction = (
                "forward" if MODE_RANK.get(to_mode, 0) > MODE_RANK.get(from_mode, 0)
                else "backward" if MODE_RANK.get(to_mode, 0) < MODE_RANK.get(from_mode, 0)
                else "lateral"
            )
            transition_rows.append(
                {
                    **base,
                    "from_mode": from_mode,
                    "to_mode": to_mode,
                    "transition": f"{from_mode} -> {to_mode}",
                    "direction": direction,
                    "position": row["position"],
                    "depth": row["depth"],
                    "pre_3s_events": len(before),
                    "pre_3s_candidate_changes": int((before["event"] == "candidate_changed").sum()),
                    "pre_3s_path_distance": pre_path,
                    "pre_3s_position_delta": row["position"] - before["position"].iloc[0] if len(before) else math.nan,
                    "pre_3s_depth_delta": row["depth"] - before["depth"].iloc[0] if len(before) else math.nan,
                }
            )
        session_rows[-1]["forward_mode_transitions"] = sum(
            row["direction"] == "forward" for row in transition_rows if row["source_file"] == base["source_file"]
        )
        session_rows[-1]["backward_mode_transitions"] = sum(
            row["direction"] == "backward" for row in transition_rows if row["source_file"] == base["source_file"]
        )
        for _, row in frame.iterrows():
            position_rows.append(
                {
                    **base,
                    "timestamp_utc": row["timestamp_utc"],
                    "seconds_from_active_start": (row["timestamp_utc"] - active_start).total_seconds(),
                    "event": row["event"],
                    "mode": row["mode"],
                    "position": row["position"],
                    "depth": row["depth"],
                }
            )

    session_df = pd.DataFrame(session_rows)
    answer_df = pd.DataFrame(answer_rows)
    event_df = pd.DataFrame(event_rows)
    mode_df = pd.DataFrame(mode_rows)
    transition_df = pd.DataFrame(transition_rows)
    position_df = pd.DataFrame(position_rows)
    touch_df = pd.DataFrame(touch_rows)
    quality_df = pd.DataFrame(quality_rows)

    numeric_metrics = session_df.select_dtypes(include=np.number).columns.difference(
        ["participant", "participant_session", "condition_session"]
    )
    participant_condition = session_df.groupby(["participant", "participant_order", "condition"], as_index=False)[
        numeric_metrics
    ].mean()
    answer_participant_condition = answer_df.groupby(
        ["participant", "participant_order", "condition"], as_index=False
    ).agg(
        task_completion_time_s=("answer_latency_s", "mean"),
        wrong_candidate_visit_events_proxy=("wrong_candidate_visit_events_proxy", "mean"),
        wrong_unique_candidates_proxy=("wrong_unique_candidates_proxy", "mean"),
        wrong_detail_visits_proxy=("wrong_detail_visits_proxy", "mean"),
        wrong_selection_confirmations_proxy=("wrong_selection_confirmations_proxy", "mean"),
        wrong_touches_per_task_rule=("wrong_touches_rule", "mean"),
        wrong_selection_touches_per_task_rule=("wrong_selection_touches_rule", "mean"),
    )
    participant_condition = participant_condition.merge(
        answer_participant_condition,
        on=["participant", "participant_order", "condition"],
        how="left",
    )
    condition_summary = session_df.groupby("condition")[numeric_metrics].agg(["mean", "std", "median", "min", "max"])
    tests = pd.DataFrame(
        paired_test(participant_condition, metric)
        for metric in [
            "active_duration_s",
            "task_completion_time_s",
            "time_to_first_answer_s",
            "time_to_second_answer_s",
            "candidate_changes",
            "mode_changes",
            "forward_mode_transitions",
            "backward_mode_transitions",
            "detail_entries",
            "pose_losses",
            "path_distance_position_depth",
            "correct_alignment_rate",
            "selection_accuracy",
            "wrong_candidate_visit_events_proxy",
            "wrong_unique_candidates_proxy",
            "wrong_detail_visits_proxy",
            "wrong_selection_confirmations_proxy",
            "wrong_touches_rule",
            "wrong_touch_rate_rule",
            "wrong_selection_touches_rule",
        ]
        if metric in participant_condition.columns
    )

    session_df.to_csv(OUT_DIR / "session_metrics.csv", index=False)
    answer_df.to_csv(OUT_DIR / "answer_metrics.csv", index=False)
    event_df.to_csv(OUT_DIR / "event_counts.csv", index=False)
    mode_df.to_csv(OUT_DIR / "mode_durations.csv", index=False)
    transition_df.to_csv(OUT_DIR / "mode_transitions.csv", index=False)
    position_df.to_csv(OUT_DIR / "position_observations.csv", index=False)
    touch_df.to_csv(OUT_DIR / "wrong_touch_classification.csv", index=False)
    participant_condition.to_csv(OUT_DIR / "participant_condition_summary.csv", index=False)
    condition_summary.to_csv(OUT_DIR / "condition_summary.csv")
    tests.to_csv(OUT_DIR / "paired_tests.csv", index=False)
    quality_df.to_csv(OUT_DIR / "data_quality.csv", index=False)

    plot_metrics = [
        ("active_duration_s", "Active duration (s)"),
        ("time_to_first_answer_s", "Time to first answer (s)"),
        ("time_to_second_answer_s", "Time between answers (s)"),
        ("candidate_changes", "Candidate changes"),
        ("detail_entries", "Detail entries"),
        ("pose_losses", "Pose losses"),
        ("path_distance_position_depth", "Position/depth path distance"),
        ("selection_accuracy", "Selection accuracy"),
    ]
    fig, axes = plt.subplots(2, 4, figsize=(18, 9))
    for ax, (metric, title) in zip(axes.flat, plot_metrics):
        sns.pointplot(data=participant_condition, x="condition", y=metric, errorbar=("ci", 95), capsize=.15, ax=ax)
        sns.stripplot(data=participant_condition, x="condition", y=metric, hue="participant", palette="tab10", ax=ax, legend=False)
        ax.set_title(title)
        ax.set_xlabel("")
    fig.suptitle("Condition comparison: participant-level means with 95% CI", fontsize=16)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "condition_comparison.png", dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(13, 10))
    for ax, (metric, title) in zip(axes.flat, plot_metrics[:4]):
        pivot = participant_condition.pivot(index="participant", columns="condition", values=metric)
        for participant, row in pivot.iterrows():
            ax.plot(CONDITIONS, row[CONDITIONS], marker="o", alpha=.75, label=f"P{participant}")
        ax.set_title(title)
        ax.set_xlabel("")
    axes[0, 0].legend(ncol=2, fontsize=8)
    fig.suptitle("Paired participant trajectories", fontsize=16)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "paired_participant_trajectories.png", dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    for ax, metric, title in zip(
        axes,
        ["active_duration_s", "candidate_changes", "selection_accuracy"],
        ["Active duration", "Candidate changes", "Selection accuracy"],
    ):
        sns.lineplot(data=session_df, x="condition_session", y=metric, hue="condition", marker="o", errorbar=("ci", 95), ax=ax)
        ax.set_title(title)
        ax.set_xticks([1, 2, 3])
    fig.suptitle("Within-condition session-order trend", fontsize=16)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "session_order_trends.png", dpi=180)
    plt.close(fig)

    mode_plot = mode_df.groupby(["condition", "mode"], as_index=False)["duration_s"].mean()
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=mode_plot, x="condition", y="duration_s", hue="mode", hue_order=MODE_ORDER, ax=ax)
    ax.set_title("Mean time spent in interaction modes per session")
    ax.set_ylabel("Duration (s)")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "mode_duration.png", dpi=180)
    plt.close(fig)

    corr_cols = [
        "active_duration_s", "candidate_changes", "detail_entries", "pose_losses",
        "path_distance_position_depth", "correct_alignment_rate",
    ]
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(session_df[corr_cols].corr(), annot=True, fmt=".2f", cmap="vlag", center=0, ax=ax)
    ax.set_title("Session-level metric correlations")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "metric_correlations.png", dpi=180)
    plt.close(fig)

    transition_counts = transition_df.groupby(["condition", "transition"], as_index=False).size()
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    for ax, condition in zip(axes, CONDITIONS):
        subset = transition_counts[transition_counts["condition"] == condition].sort_values("size", ascending=False)
        sns.barplot(data=subset, y="transition", x="size", ax=ax)
        ax.set_title(condition)
        ax.set_xlabel("Transition count")
        ax.set_ylabel("")
    fig.suptitle("Observed mode transition paths", fontsize=16)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "mode_transition_paths.png", dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(2, 4, figsize=(18, 9), sharex=True, sharey=True)
    for row_idx, condition in enumerate(CONDITIONS):
        for col_idx, mode in enumerate(MODE_ORDER):
            ax = axes[row_idx, col_idx]
            subset = position_df[(position_df["condition"] == condition) & (position_df["mode"] == mode)]
            if len(subset):
                ax.hexbin(subset["position"], subset["depth"], gridsize=18, cmap="magma", mincnt=1)
            ax.set_title(f"{condition}: {mode}")
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.set_xlabel("camera-space position")
            ax.set_ylabel("camera-space depth")
    fig.suptitle("Event-sampled position/depth heatmaps", fontsize=16)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "position_depth_heatmaps.png", dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharex=True, sharey=True)
    for ax, condition in zip(axes, CONDITIONS):
        subset = position_df[position_df["condition"] == condition]
        for _, session in subset.groupby("source_file"):
            ax.plot(session["position"], session["depth"], alpha=.25, linewidth=1)
            ax.scatter(session["position"].iloc[0], session["depth"].iloc[0], s=12, color="green", alpha=.5)
        ax.set_title(condition)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xlabel("camera-space position")
        ax.set_ylabel("camera-space depth")
    fig.suptitle("Event-sampled movement trajectories (green = session start)", fontsize=16)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "movement_trajectories.png", dpi=180)
    plt.close(fig)

    transition_pre = transition_df.groupby(["condition", "direction"], as_index=False).agg(
        transitions=("transition", "size"),
        pre_3s_candidate_changes=("pre_3s_candidate_changes", "mean"),
        pre_3s_path_distance=("pre_3s_path_distance", "mean"),
        pre_3s_depth_delta=("pre_3s_depth_delta", "mean"),
    )
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    for ax, metric, title in zip(
        axes,
        ["pre_3s_candidate_changes", "pre_3s_path_distance", "pre_3s_depth_delta"],
        ["Candidate changes in prior 3 s", "Path distance in prior 3 s", "Depth change in prior 3 s"],
    ):
        sns.barplot(data=transition_pre, x="direction", y=metric, hue="condition", ax=ax)
        ax.set_title(title)
        ax.set_xlabel("")
    fig.suptitle("Behavior immediately before mode transitions", fontsize=16)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "pre_transition_behavior.png", dpi=180)
    plt.close(fig)

    answer_summary = answer_df.groupby("condition").agg(
        task_completion_time_s=("answer_latency_s", "mean"),
        wrong_candidate_visit_events_proxy=("wrong_candidate_visit_events_proxy", "mean"),
        wrong_unique_candidates_proxy=("wrong_unique_candidates_proxy", "mean"),
        wrong_detail_visits_proxy=("wrong_detail_visits_proxy", "mean"),
        wrong_selection_confirmations_proxy=("wrong_selection_confirmations_proxy", "mean"),
        wrong_touches_rule=("wrong_touches_rule", "mean"),
        wrong_selection_touches_rule=("wrong_selection_touches_rule", "mean"),
    )
    answer_summary.to_csv(OUT_DIR / "task_and_wrong_visit_summary.csv")

    wrong_touch_plot = answer_df.groupby("condition", as_index=False).agg(
        wrong_touches_rule=("wrong_touches_rule", "mean"),
        wrong_selection_touches_rule=("wrong_selection_touches_rule", "mean"),
    ).melt(id_vars="condition", var_name="metric", value_name="mean_per_task")
    fig, ax = plt.subplots(figsize=(9, 6))
    sns.barplot(data=wrong_touch_plot, x="metric", y="mean_per_task", hue="condition", ax=ax)
    ax.set_title("Wrong touches: no space_pressed before the next touch")
    ax.set_xlabel("")
    ax.set_ylabel("Mean wrong touches per task")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "wrong_touches_rule.png", dpi=180)
    plt.close(fig)

    wrong_plot = answer_summary.reset_index().melt(
        id_vars="condition",
        value_vars=[
            "wrong_candidate_visit_events_proxy",
            "wrong_unique_candidates_proxy",
            "wrong_detail_visits_proxy",
            "wrong_selection_confirmations_proxy",
        ],
        var_name="metric",
        value_name="mean_per_task",
    )
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(data=wrong_plot, x="metric", y="mean_per_task", hue="condition", ax=ax)
    ax.set_title("Wrong-visit proxies per task")
    ax.set_xlabel("")
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "wrong_visit_proxies.png", dpi=180)
    plt.close(fig)

    compact = participant_condition.groupby("condition").agg(
        active_duration_s=("active_duration_s", "mean"),
        first_answer_s=("time_to_first_answer_s", "mean"),
        between_answers_s=("time_to_second_answer_s", "mean"),
        candidate_changes=("candidate_changes", "mean"),
        pose_losses=("pose_losses", "mean"),
        alignment_rate=("correct_alignment_rate", "mean"),
        selection_accuracy=("selection_accuracy", "mean"),
    )
    report = [
        "# User event log quantitative analysis",
        "",
        "## Design and interpretation",
        "",
        "- 36 sessions: 6 participants x 6 sessions.",
        "- Conditions: MoveDistance and ScreenTouch, 3 sessions per participant per condition.",
        "- Participants were inferred from chronological blocks of six sessions.",
        "- `space_pressed` is treated as the answer timestamp.",
        "- Every `space_pressed` is a correct answer, so selection accuracy is correct space presses / all space presses.",
        "- Candidate-selected equality is reported separately as selection alignment/consistency.",
        "",
        "## Participant-level condition means",
        "",
        compact.round(3).to_markdown(),
        "",
        "## Paired condition tests",
        "",
        tests.round(4).to_markdown(index=False),
        "",
        "## Data quality",
        "",
        f"- Parsed {quality_df['rows'].sum():,} event rows.",
        f"- Repaired {quality_df['repaired_rows'].sum()} malformed `space_pressed` rows in the first two logs.",
        f"- Sessions with exactly two `space_pressed` events: {(quality_df['space_pressed_count'] == 2).sum()} / 36.",
        "",
        "See the CSV files for all session-, answer-, event-, mode-, and participant-level metrics.",
    ]
    (OUT_DIR / "analysis_report.md").write_text("\n".join(report), encoding="utf-8")

    print(f"Wrote analysis to {OUT_DIR}")
    print(compact.round(3))
    print(tests[["metric", "mean_difference_Move_minus_Touch", "paired_t_p", "cohen_dz"]].round(4))


if __name__ == "__main__":
    main()
