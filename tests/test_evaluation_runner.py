
from src.evaluation.runner import evaluate_solver
from src.models.entities import (
    SchedulingProblem,
    Subject,
    SubjectRequirement,
    Teacher,
    StudentGroup,
    Room,
    TimeStructure,
)
from src.models.schedule import Assignment, ScheduledSession, Timetable


def make_problem():
    return SchedulingProblem(
        subjects=[Subject("MATH", "Mathematics")],
        teachers=[
            Teacher(
                "T1",
                "Teacher One",
                ["MATH"],
                maximum_weekly_load=2,
            )
        ],
        student_groups=[
            StudentGroup(
                "G1",
                "Group One",
                30,
                [SubjectRequirement("MATH", 2, 1)],
                [4],
            )
        ],
        rooms=[Room("R1", "Room One", 40, "classroom")],
        time_structure=TimeStructure(["Monday", "Tuesday"], 6),
    )


def make_valid_timetable():
    sessions = []

    for session_id, day in [
        ("S1", "Monday"),
        ("S2", "Tuesday"),
    ]:
        assignment = Assignment(
            session_id=session_id,
            teacher_id="T1",
            day=day,
            start_period=1,
            room_id="R1",
        )
        sessions.append(
            ScheduledSession(
                session_id=session_id,
                group_id="G1",
                subject_id="MATH",
                duration_slots=1,
                assignment=assignment,
            )
        )

    return Timetable(sessions)


def test_evaluate_solver_scores_valid_timetable():
    problem = make_problem()
    timetable = make_valid_timetable()

    result = evaluate_solver(lambda _: timetable, problem)

    assert result.success is True
    assert result.hard_violations == []
    assert result.soft_penalties is not None
    assert result.total_soft_penalty == 0
    assert result.timetable is timetable
    assert result.runtime_seconds >= 0


def test_evaluate_solver_handles_no_solution():
    result = evaluate_solver(lambda _: None, make_problem())

    assert result.success is False
    assert result.timetable is None
    assert result.soft_penalties is None
    assert result.hard_violations == [
        "Solver did not find a timetable."
    ]


def test_evaluate_solver_rejects_invalid_timetable():
    problem = make_problem()
    valid_timetable = make_valid_timetable()

    # Both sessions now overlap for the same teacher and student group.
    valid_timetable.sessions[1].assignment = Assignment(
        session_id="S2",
        teacher_id="T1",
        day="Monday",
        start_period=1,
        room_id="R1",
    )

    result = evaluate_solver(lambda _: valid_timetable, problem)

    assert result.success is False
    assert result.hard_violations
    assert result.soft_penalties is None
    assert result.timetable is valid_timetable


def test_evaluate_solver_passes_custom_weights():
    problem = make_problem()
    timetable = make_valid_timetable()

    result = evaluate_solver(
        lambda _: timetable,
        problem,
        weights={"class_gaps": 3},
    )

    assert result.success is True
    assert result.total_soft_penalty == 0
