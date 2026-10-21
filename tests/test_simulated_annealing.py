
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
from src.solvers.simulated_annealing import solve, solve_with_stats


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


def test_simulated_annealing_finds_valid_timetable():
    problem = make_problem()

    result = solve_with_stats(problem, seed=7)

    assert isinstance(result.timetable, Timetable)
    assert validate_timetable(result.timetable, problem) == []
    assert len(result.timetable.sessions) == 2
    assert result.stats.iterations > 0


def test_simulated_annealing_returns_none_for_empty_domain():
    problem = make_problem()
    problem.time_structure.working_days = []

    result = solve_with_stats(problem, seed=7)

    assert result.timetable is None


def test_simulated_annealing_simple_interface():
    result = solve(make_problem())

    assert isinstance(result, Timetable)


def test_simulated_annealing_rejects_invalid_parameters():
    problem = make_problem()

    try:
        solve_with_stats(problem, max_steps=0)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for max_steps=0")


def test_simulated_annealing_returns_none_when_no_schedule_is_possible():
    problem = make_problem()
    problem.time_structure.working_days = ["Monday"]
    problem.time_structure.periods_per_day = 1
    problem.student_groups[0].subject_requirements = [
        SubjectRequirement("MATH", 2, 1)
    ]

    result = solve_with_stats(
        problem,
        max_steps=50,
        max_restarts=1,
        seed=7,
    )

    assert result.timetable is None
