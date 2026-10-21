from src.models.entities import (
    SchedulingProblem,
    Subject,
    SubjectRequirement,
    Teacher,
    StudentGroup,
    Room,
    TimeStructure,
)
from src.solvers.backtracking import (
    _is_consistent,
    _make_scheduled_session,
)
from src.models.schedule import Assignment, ScheduledSession
from src.models.entities import SchedulingProblem, Subject, Teacher, StudentGroup, Room, TimeStructure
from src.solvers.backtracking import solve
from src.evaluation.validator import validate_timetable

def make_problem():
    return SchedulingProblem(
        subjects=[Subject("MATH", "Mathematics")],
        teachers=[Teacher("T1", "Teacher One", ["MATH"])],
        student_groups=[
            StudentGroup(
                "G1",
                "Group One",
                30,
                subject_requirements=[
                    SubjectRequirement("MATH", weekly_sessions=2)
                ],
            )
        ],
        rooms=[Room("R1", "Room One", 40, "classroom")],
        time_structure=TimeStructure(["Monday", "Tuesday"], 6),
    )


def test_consistent_candidate_is_accepted():
    problem = make_problem()

    candidate = ScheduledSession(
        session_id="S1",
        group_id="G1",
        subject_id="MATH",
        duration_slots=1,
        assignment=Assignment("S1", "T1", "Monday", 1, "R1"),
    )

    assert _is_consistent(candidate, [], problem)


def test_teacher_conflict_is_rejected():
    problem = make_problem()

    existing = ScheduledSession(
        session_id="S1",
        group_id="G1",
        subject_id="MATH",
        duration_slots=1,
        assignment=Assignment("S1", "T1", "Monday", 1, "R1"),
    )

    candidate = ScheduledSession(
        session_id="S2",
        group_id="G2",
        subject_id="MATH",
        duration_slots=1,
        assignment=Assignment("S2", "T1", "Monday", 1, "R1"),
    )

    assert not _is_consistent(candidate, [existing], problem)


def test_solver_generates_valid_timetable():
    problem = make_problem()

    timetable = solve(problem)

    assert timetable is not None
    assert len(timetable.sessions) == 2
    assert validate_timetable(timetable, problem) == []
