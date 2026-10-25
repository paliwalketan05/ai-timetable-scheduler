
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
from src.solvers.hybrid import solve, solve_with_stats


def make_problem():
    return SchedulingProblem(
        subjects=[Subject("MATH", "Mathematics")],
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


def test_hybrid_finds_valid_timetable():
    problem = make_problem()

    result = solve_with_stats(problem, max_steps=100, seed=7)

    assert isinstance(result.timetable, Timetable)
    assert validate_timetable(result.timetable, problem) == []
    assert len(result.timetable.sessions) == 2
    assert result.stats.backtracking_nodes > 0


def test_hybrid_simple_interface():
    result = solve(make_problem())

    assert isinstance(result, Timetable)


def test_hybrid_returns_none_when_no_solution_exists():
    problem = make_problem()
    problem.time_structure.working_days = []
    result = solve_with_stats(problem, max_steps=100, seed=7)

    assert result.timetable is None
