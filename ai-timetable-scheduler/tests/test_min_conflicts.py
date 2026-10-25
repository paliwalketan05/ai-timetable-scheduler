from src.solvers.min_conflicts import _conflict_count
from src.solvers.heuristics import make_scheduled_session
from src.csp.sessions import expand_sessions
from src.csp.domains import generate_domains
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
from src.models.schedule import Timetable
from src.solvers.min_conflicts import solve, solve_with_stats


def make_problem():
    return SchedulingProblem(
        subjects=[Subject("MATH", "Mathematics", "theory")],
        teachers=[
            Teacher("T1", "Teacher One", ["MATH"], maximum_weekly_load=5)
        ],
        student_groups=[
            StudentGroup(
                "G1",
                "Group One",
                30,
                [SubjectRequirement("MATH", 2, 1)],
            )
        ],
        rooms=[Room("R1", "Room One", 40, "classroom")],
        time_structure=TimeStructure(["Monday", "Tuesday"], 4),
    )


def test_min_conflicts_finds_valid_timetable():
    problem = make_problem()

    result = solve_with_stats(problem, seed=7)

    assert isinstance(result.timetable, Timetable)
    assert validate_timetable(result.timetable, problem) == []
    assert len(result.timetable.sessions) == 2


def test_min_conflicts_returns_none_when_domain_is_empty():
    problem = make_problem()
    problem.time_structure.working_days = []

    result = solve_with_stats(problem, seed=7)

    assert result.timetable is None


def test_min_conflicts_simple_interface():
    result = solve(make_problem())

    assert isinstance(result, Timetable)


def test_min_conflicts_rejects_invalid_search_limits():
    problem = make_problem()

    try:
        solve_with_stats(problem, max_steps=0)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for max_steps=0")


def test_min_conflicts_does_not_return_invalid_timetable():
    problem = make_problem()
    # Two required sessions, but only one available period.
    problem.time_structure.working_days = ["Monday"]
    problem.time_structure.periods_per_day = 1
    problem.student_groups[0].subject_requirements = [
        SubjectRequirement("MATH", 2, 1)
    ]

    result = solve_with_stats(
        problem,
        max_steps=20,
        max_restarts=2,
        seed=7,
    )

    assert result.timetable is None


def test_conflict_count_detects_teacher_workload_excess():
    problem = make_problem()
    problem.teachers[0].maximum_weekly_load = 1

    sessions = expand_sessions(problem)
    domains = generate_domains(problem, sessions)

    first = make_scheduled_session(sessions[0], domains[sessions[0].id][0])
    second = make_scheduled_session(sessions[1], domains[sessions[1].id][0])

    # Score the second session against the first. The teacher's combined
    # workload is two periods, exceeding the configured maximum of one.
    score = _conflict_count(second, [first], problem)

    assert score >= 1


def test_conflict_count_detects_overlapping_group_sessions():
    problem = make_problem()
    sessions = expand_sessions(problem)
    domains = generate_domains(problem, sessions)

    first_assignment = domains[sessions[0].id][0]
    overlapping_assignment = next(
        assignment
        for assignment in domains[sessions[1].id]
        if assignment.day == first_assignment.day
        and assignment.start_period == first_assignment.start_period
    )

    first = make_scheduled_session(sessions[0], first_assignment)
    second = make_scheduled_session(sessions[1], overlapping_assignment)

    assert _conflict_count(second, [first], problem) >= 1
