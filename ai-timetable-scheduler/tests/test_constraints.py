from src.csp.constraints import (
    has_teacher_conflict,
    has_group_conflict,
    has_room_conflict,
    has_room_capacity_violation,
    has_room_type_violation,
    has_teacher_availability_violation,
    _sessions_overlap,
)
from src.models.entities import (
    Room,
    SchedulingProblem,
    StudentGroup,
    Subject,
    Teacher,
    TimeStructure,
)
from src.models.schedule import Assignment, ScheduledSession


def make_session(
    session_id="S1",
    group_id="G1",
    subject_id="SUB1",
    duration=1,
    teacher_id="T1",
    day="Monday",
    start_period=1,
    room_id="R1",
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
            room_id=room_id,
        ),
    )


def make_problem():
    return SchedulingProblem(
        subjects=[Subject("SUB1", "Mathematics", "theory")],
        teachers=[Teacher("T1", "Teacher One", ["SUB1"], ["Monday_P2"], 20)],
        student_groups=[StudentGroup("G1", "Group One", 30)],
        rooms=[Room("R1", "Room One", 40, "classroom")],
        time_structure=TimeStructure(["Monday", "Tuesday"], 6),
    )


def test_sessions_overlap():
    a = make_session(duration=2, start_period=2)
    b = make_session(session_id="S2", start_period=3)
    c = make_session(session_id="S3", day="Tuesday", start_period=3)

    assert _sessions_overlap(a, b)
    assert not _sessions_overlap(a, c)


def test_teacher_conflict():
    candidate = make_session()
    existing = make_session(session_id="S2", group_id="G2")

    assert has_teacher_conflict(candidate, [existing])


def test_group_conflict():
    candidate = make_session()
    existing = make_session(session_id="S2", teacher_id="T2")

    assert has_group_conflict(candidate, [existing])


def test_room_conflict():
    candidate = make_session()
    existing = make_session(session_id="S2", teacher_id="T2", group_id="G2")

    assert has_room_conflict(candidate, [existing])


def test_room_capacity_violation():
    problem = make_problem()
    candidate = make_session()

    problem.rooms[0].capacity = 20

    assert has_room_capacity_violation(candidate, problem)


def test_room_type_violation():
    problem = make_problem()
    candidate = make_session()

    problem.subjects[0].subject_type = "lab"

    assert has_room_type_violation(candidate, problem)


def test_teacher_availability_violation():
    problem = make_problem()
    candidate = make_session(start_period=2)

    assert has_teacher_availability_violation(candidate, problem)


def test_teacher_availability_allows_available_period():
    problem = make_problem()
    candidate = make_session(start_period=3)

    assert not has_teacher_availability_violation(candidate, problem)