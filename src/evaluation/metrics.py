
"""Soft-constraint metrics for timetable quality."""

from collections import defaultdict

from src.models.schedule import Timetable


def _occupied_periods(start_period: int, duration_slots: int) -> set[int]:
    """Return every period occupied by a session."""
    return set(range(start_period, start_period + duration_slots))


def class_gap_penalty(timetable: Timetable) -> int:
    """Count empty periods between sessions for each group and day."""
    occupied_by_group_day: dict[tuple[str, str], set[int]] = defaultdict(set)

    for session in timetable.sessions:
        assignment = session.assignment
        key = (session.group_id, assignment.day)
        occupied_by_group_day[key].update(
            _occupied_periods(
                assignment.start_period,
                session.duration_slots,
            )
        )

    penalty = 0

    for occupied in occupied_by_group_day.values():
        if occupied:
            penalty += max(occupied) - min(occupied) + 1 - len(occupied)

    return penalty


def subject_distribution_penalty(timetable: Timetable) -> int:
    """Penalize multiple sessions of the same subject for a group on one day."""
    counts: dict[tuple[str, str, str], int] = defaultdict(int)

    for session in timetable.sessions:
        key = (
            session.group_id,
            session.subject_id,
            session.assignment.day,
        )
        counts[key] += 1

    return sum(count - 1 for count in counts.values() if count > 1)


def teacher_consecutive_penalty(
    timetable: Timetable,
    max_consecutive: int = 2,
) -> int:
    """Count teacher periods beyond the consecutive-period limit."""
    if max_consecutive < 1:
        raise ValueError("max_consecutive must be at least 1")

    occupied_by_teacher_day: dict[tuple[str, str], set[int]] = defaultdict(set)

    for session in timetable.sessions:
        assignment = session.assignment
        key = (assignment.teacher_id, assignment.day)
        occupied_by_teacher_day[key].update(
            _occupied_periods(
                assignment.start_period,
                session.duration_slots,
            )
        )

    penalty = 0

    for occupied in occupied_by_teacher_day.values():
        consecutive = 0

        for period in sorted(occupied):
            if period - 1 in occupied:
                consecutive += 1
            else:
                consecutive = 1

            if consecutive > max_consecutive:
                penalty += 1

    return penalty


def calculate_soft_penalty(
    timetable: Timetable,
    weights: dict[str, int] | None = None,
) -> dict[str, int]:
    """Return individual soft penalties and their weighted total."""
    selected_weights = {
        "class_gaps": 1,
        "subject_distribution": 1,
        "teacher_consecutive": 1,
    }

    if weights is not None:
        unknown = set(weights) - set(selected_weights)
        if unknown:
            raise ValueError(f"Unknown penalty weights: {sorted(unknown)}")

        for name, weight in weights.items():
            if weight < 0:
                raise ValueError(f"Weight for {name} cannot be negative")
            selected_weights[name] = weight

    penalties = {
        "class_gaps": class_gap_penalty(timetable),
        "subject_distribution": subject_distribution_penalty(timetable),
        "teacher_consecutive": teacher_consecutive_penalty(timetable),
    }

    penalties["total"] = sum(
        penalties[name] * selected_weights[name]
        for name in selected_weights
    )

    return penalties
