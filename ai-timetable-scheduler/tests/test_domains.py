
from src.csp.domains import generate_domains
from src.csp.sessions import SchedulingSession
from src.models.entities import (
    Room,
    SchedulingProblem,
    StudentGroup,
    Subject,
    Teacher,
    TimeStructure,
)


def make_problem():
    return SchedulingProblem(
        subjects=[
            Subject("MAT101", "Mathematics", "theory"),
            Subject("CHEM101", "Chemistry", "lab"),
        ],
        teachers=[
            Teacher("T1", "Teacher One", ["MAT101"], ["Monday_P1"], 20),
            Teacher("T2", "Teacher Two", ["CHEM101"], [], 20),
        ],
        student_groups=[
            StudentGroup(
                "CS-A",
                "Computer Science A",
                25,
                lunch_break_periods=[3],
            )
        ],
        rooms=[
            Room("R1", "Classroom 1", 30, "classroom"),
            Room("R2", "Small Classroom", 20, "classroom"),
            Room("R3", "Lab 1", 30, "lab"),
        ],
        time_structure=TimeStructure(
            working_days=["Monday"],
            periods_per_day=4,
            break_periods=[2],
        ),
    )


def test_domain_excludes_unavailable_teacher_slots():
    problem = make_problem()
    session = SchedulingSession("S1", "CS-A", "MAT101", 1)

    domain = generate_domains(problem, [session])["S1"]

    assert all(
        not (item.day == "Monday" and item.start_period == 1)
        for item in domain
    )


def test_domain_excludes_break_and_lunch_periods():
    problem = make_problem()
    session = SchedulingSession("S1", "CS-A", "MAT101", 1)

    domain = generate_domains(problem, [session])["S1"]

    assert all(item.start_period not in {2, 3} for item in domain)


def test_domain_respects_room_capacity_and_type():
    problem = make_problem()
    session = SchedulingSession("S1", "CS-A", "MAT101", 1)

    domain = generate_domains(problem, [session])["S1"]

    assert domain
    assert {item.room_id for item in domain} == {"R1"}



def test_lab_session_requires_lab_room_and_consecutive_periods():
    problem = make_problem()

    # Give the lab a valid two-period window.
    problem.time_structure.break_periods = []
    problem.student_groups[0].lunch_break_periods = []

    session = SchedulingSession("S2", "CS-A", "CHEM101", 2)

    domain = generate_domains(problem, [session])["S2"]

    assert domain
    assert {item.room_id for item in domain} == {"R3"}
    assert all(item.start_period <= 3 for item in domain)

from src.models.schedule import Assignment, ScheduledSession, Timetable


def test_timetable_returns_selected_assignments():
    assignment = Assignment(
        session_id="S1",
        teacher_id="T1",
        day="Monday",
        start_period=1,
        room_id="R1",
    )

    scheduled_session = ScheduledSession(
        session_id="S1",
        group_id="CS-A",
        subject_id="MAT101",
        duration_slots=1,
        assignment=assignment,
    )

    timetable = Timetable(sessions=[scheduled_session])

    assert timetable.assignments() == [assignment]