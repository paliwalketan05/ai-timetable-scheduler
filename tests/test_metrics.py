
import pytest

from src.evaluation.metrics import (
    calculate_soft_penalty,
    class_gap_penalty,
    subject_distribution_penalty,
    teacher_consecutive_penalty,
)
from src.models.schedule import Assignment, ScheduledSession, Timetable


def make_session(
    session_id,
    group_id,
    subject_id,
    teacher_id,
    day,
    start_period,
    duration=1,
):
    return ScheduledSession(
        session_id=session_id,
        group_id=group_id,
        subject_id=subject_id,
        duration_slots=duration,
        assignment=Assignment(
            session_id=session_id,
            teacher_id=teacher_id,
            day=day,
            start_period=start_period,
            room_id="R1",
        ),
    )


def test_class_gap_penalty():
    timetable = Timetable([
        make_session("S1", "G1", "MATH", "T1", "Monday", 1),
        make_session("S2", "G1", "ENG", "T2", "Monday", 3),
    ])

    assert class_gap_penalty(timetable) == 1


def test_class_gap_penalty_handles_lab_duration():
    timetable = Timetable([
        make_session("S1", "G1", "LAB", "T1", "Monday", 1, duration=2),
        make_session("S2", "G1", "MATH", "T2", "Monday", 4),
    ])

    assert class_gap_penalty(timetable) == 1


def test_subject_distribution_penalty():
    timetable = Timetable([
        make_session("S1", "G1", "MATH", "T1", "Monday", 1),
        make_session("S2", "G1", "MATH", "T2", "Monday", 3),
        make_session("S3", "G1", "MATH", "T1", "Tuesday", 1),
    ])

    assert subject_distribution_penalty(timetable) == 1


def test_teacher_consecutive_penalty():
    timetable = Timetable([
        make_session("S1", "G1", "MATH", "T1", "Monday", 1),
        make_session("S2", "G2", "ENG", "T1", "Monday", 2),
        make_session("S3", "G3", "SCI", "T1", "Monday", 3),
        make_session("S4", "G4", "HIST", "T1", "Monday", 4),
    ])

    assert teacher_consecutive_penalty(timetable) == 2


def test_teacher_consecutive_penalty_resets_after_gap():
    timetable = Timetable([
        make_session("S1", "G1", "MATH", "T1", "Monday", 1),
        make_session("S2", "G2", "ENG", "T1", "Monday", 2),
        make_session("S3", "G3", "SCI", "T1", "Monday", 4),
        make_session("S4", "G4", "HIST", "T1", "Monday", 5),
    ])

    assert teacher_consecutive_penalty(timetable) == 0


def test_combined_penalty_uses_weights():
    timetable = Timetable([
        make_session("S1", "G1", "MATH", "T1", "Monday", 1),
        make_session("S2", "G1", "ENG", "T2", "Monday", 3),
    ])

    result = calculate_soft_penalty(
        timetable,
        weights={"class_gaps": 3},
    )

    assert result == {
        "class_gaps": 1,
        "subject_distribution": 0,
        "teacher_consecutive": 0,
        "total": 3,
    }


def test_negative_weight_is_rejected():
    with pytest.raises(ValueError):
        calculate_soft_penalty(
            Timetable([]),
            weights={"class_gaps": -1},
        )


def test_unknown_weight_is_rejected():
    with pytest.raises(ValueError):
        calculate_soft_penalty(
            Timetable([]),
            weights={"made_up_metric": 1},
        )
