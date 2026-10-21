from src.evaluation.validator import validate_timetable
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


def make_session(session_id, day, period, duration=1):
    return ScheduledSession(
        session_id=session_id,
        group_id="G1",
        subject_id="MATH",
        duration_slots=duration,
        assignment=Assignment(
            session_id=session_id,
            teacher_id="T1",
            day=day,
            start_period=period,
            room_id="R1",
        ),
    )


def test_valid_timetable_has_no_violations():
    problem = make_problem()
    timetable = Timetable([
        make_session("S1", "Monday", 1),
        make_session("S2", "Tuesday", 1),
    ])

    assert validate_timetable(timetable, problem) == []


def test_h7_detects_missing_weekly_session():
    problem = make_problem()
    timetable = Timetable([make_session("S1", "Monday", 1)])

    violations = validate_timetable(timetable, problem)

    assert any("Weekly session count violation" in v for v in violations)


def test_h7_detects_incorrect_total_duration():
    problem = make_problem()
    timetable = Timetable([
        make_session("S1", "Monday", 1, 2),
        make_session("S2", "Tuesday", 1),
    ])

    violations = validate_timetable(timetable, problem)

    assert any("Weekly hours violation" in v for v in violations)


def test_h8_detects_excess_teacher_workload():
    problem = make_problem()
    problem.teachers[0].maximum_weekly_load = 1
    timetable = Timetable([
        make_session("S1", "Monday", 1),
        make_session("S2", "Tuesday", 1),
    ])

    violations = validate_timetable(timetable, problem)

    assert any("Teacher workload violation" in v for v in violations)


def test_h9_detects_lunch_break_violation():
    problem = make_problem()
    timetable = Timetable([
        make_session("S1", "Monday", 4),
        make_session("S2", "Tuesday", 1),
    ])

    violations = validate_timetable(timetable, problem)

    assert any("Lunch break violation" in v for v in violations)

def test_h1_detects_teacher_conflict():
    problem = make_problem()
    timetable = Timetable([
        make_session("S1", "Monday", 1),
        make_session("S2", "Monday", 1),
    ])

    violations = validate_timetable(timetable, problem)

    assert any("Teacher conflict" in v for v in violations)


def test_h2_detects_group_conflict():
    problem = make_problem()
    timetable = Timetable([
        make_session("S1", "Monday", 1),
        make_session("S2", "Monday", 1),
    ])

    violations = validate_timetable(timetable, problem)

    assert any("Student group conflict" in v for v in violations)


def test_h3_detects_room_conflict():
    problem = make_problem()
    timetable = Timetable([
        make_session("S1", "Monday", 1),
        make_session("S2", "Monday", 1),
    ])

    violations = validate_timetable(timetable, problem)

    assert any("Room conflict" in v for v in violations)


def test_h4_detects_room_capacity_violation():
    problem = make_problem()
    problem.rooms[0].capacity = 20

    timetable = Timetable([
        make_session("S1", "Monday", 1),
        make_session("S2", "Tuesday", 1),
    ])

    violations = validate_timetable(timetable, problem)

    assert any("Room capacity violation" in v for v in violations)


def test_h5_detects_room_type_violation():
    problem = make_problem()
    problem.subjects[0].subject_type = "lab"

    timetable = Timetable([
        make_session("S1", "Monday", 1),
        make_session("S2", "Tuesday", 1),
    ])

    violations = validate_timetable(timetable, problem)

    assert any("Room type violation" in v for v in violations)


def test_h6_detects_teacher_availability_violation():
    problem = make_problem()
    problem.teachers[0].unavailable_slots = ["Monday_P2"]

    timetable = Timetable([
        make_session("S1", "Monday", 2),
        make_session("S2", "Tuesday", 1),
    ])

    violations = validate_timetable(timetable, problem)

    assert any("Teacher availability violation" in v for v in violations)


def test_rejects_period_outside_working_day():
    problem = make_problem()
    timetable = Timetable([
        make_session("S1", "Monday", 7),
        make_session("S2", "Tuesday", 1),
    ])

    violations = validate_timetable(timetable, problem)

    assert any("Invalid time slot" in v for v in violations)


def test_rejects_session_during_general_break():
    problem = make_problem()
    problem.time_structure.break_periods = [3]

    timetable = Timetable([
        make_session("S1", "Monday", 3),
        make_session("S2", "Tuesday", 1),
    ])

    violations = validate_timetable(timetable, problem)

    assert any("Break period violation" in v for v in violations)


def test_rejects_invalid_working_day():
    problem = make_problem()
    timetable = Timetable([
        make_session("S1", "Saturday", 1),
        make_session("S2", "Tuesday", 1),
    ])

    violations = validate_timetable(timetable, problem)

    assert any("Invalid working day" in v for v in violations)


def test_rejects_assignment_session_id_mismatch():
    problem = make_problem()

    session = make_session("S1", "Monday", 1)
    session.assignment = Assignment(
        session_id="DIFFERENT_ID",
        teacher_id="T1",
        day="Monday",
        start_period=1,
        room_id="R1",
    )

    timetable = Timetable([
        session,
        make_session("S2", "Tuesday", 1),
    ])

    violations = validate_timetable(timetable, problem)

    assert any("Assignment session ID mismatch" in v for v in violations)
