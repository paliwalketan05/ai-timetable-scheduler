
from src.csp.sessions import SchedulingSession
from src.models.schedule import Assignment, ScheduledSession
from src.solvers.heuristics import (
    forward_check,
    select_mrv_session,
    select_mrv_degree_session,
)
from src.solvers.heuristics import initial_domains
from src.solvers.heuristics import make_scheduled_session
from src.solvers.heuristics import is_consistent
from tests.test_domains import make_problem


def test_mrv_selects_session_with_smallest_domain():
    problem = make_problem()
    sessions = [
        SchedulingSession("S1", "CS-A", "MAT101", 1),
        SchedulingSession("S2", "CS-A", "MAT101", 1),
    ]
    domains = {
        "S1": [
            Assignment("S1", "T1", "Monday", 1, "R1"),
            Assignment("S1", "T1", "Monday", 4, "R1"),
        ],
        "S2": [Assignment("S2", "T1", "Monday", 4, "R1")],
    }

    selected = select_mrv_session(sessions, domains, [])

    assert selected.id == "S2"


def test_mrv_degree_selects_from_most_constrained_tie():
    sessions = [
        SchedulingSession("S1", "CS-A", "MAT101", 1),
        SchedulingSession("S2", "CS-A", "MAT101", 1),
        SchedulingSession("S3", "OTHER", "CHEM101", 1),
    ]
    domains = {
        "S1": [Assignment("S1", "T1", "Monday", 1, "R1")],
        "S2": [Assignment("S2", "T1", "Monday", 1, "R1")],
        "S3": [Assignment("S3", "T2", "Monday", 4, "R3")],
    }

    selected = select_mrv_degree_session(sessions, domains, [])

    assert selected.id in {"S1", "S2"}




def test_forward_check_removes_conflicting_assignments():
    problem = make_problem()
    problem.time_structure.working_days.append("Tuesday")

    sessions = [
        SchedulingSession("S1", "CS-A", "MAT101", 1),
        SchedulingSession("S2", "CS-A", "MAT101", 1),
    ]
    domains = initial_domains(problem, sessions)

    chosen = Assignment("S1", "T1", "Monday", 4, "R1")
    scheduled = [make_scheduled_session(sessions[0], chosen)]

    filtered = forward_check(sessions, domains, scheduled, problem)

    assert filtered is not None
    assert "S2" in filtered
    assert filtered["S2"]

    # The conflicting Monday-period-4 assignment must be removed.
    assert all(
        not (
            assignment.day == "Monday"
            and assignment.start_period == 4
        )
        for assignment in filtered["S2"]
    )

    # Tuesday remains available.
    assert any(
        assignment.day == "Tuesday"
        for assignment in filtered["S2"]
    )




def test_forward_check_detects_empty_domain():
    problem = make_problem()
    sessions = [
        SchedulingSession("S1", "CS-A", "MAT101", 1),
        SchedulingSession("S2", "CS-A", "MAT101", 1),
    ]
    chosen = Assignment("S1", "T1", "Monday", 1, "R1")
    scheduled = [make_scheduled_session(sessions[0], chosen)]
    domains = {
        "S1": [chosen],
        "S2": [Assignment("S2", "T1", "Monday", 1, "R1")],
    }

    assert forward_check(sessions, domains, scheduled, problem) is None
