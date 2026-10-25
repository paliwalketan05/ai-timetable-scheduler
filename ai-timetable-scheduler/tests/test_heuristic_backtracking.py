
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
from src.solvers.heuristic_backtracking import solve, solve_with_stats
from src.evaluation.validator import validate_timetable


def make_problem():
    return SchedulingProblem(
        subjects=[Subject("MATH", "Mathematics", "theory")],
        teachers=[
            Teacher(
                "T1",
                "Teacher One",
                ["MATH"],
                maximum_weekly_load=5,
            )
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
        time_structure=TimeStructure(
            ["Monday", "Tuesday"],
            4,
        ),
    )


def test_heuristic_solver_finds_valid_timetable():
    problem = make_problem()

    result = solve_with_stats(problem)

    assert isinstance(result.timetable, Timetable)
    assert validate_timetable(result.timetable, problem) == []
    assert len(result.timetable.sessions) == 2
    assert result.stats.nodes_explored > 0


def test_solve_returns_timetable_or_none():
    result = solve(make_problem())

    assert isinstance(result, Timetable)


def test_heuristic_solver_reports_no_solution():
    problem = make_problem()
    problem.time_structure.working_days = ["Monday"]
    problem.time_structure.periods_per_day = 1
    problem.student_groups[0].subject_requirements = [
        SubjectRequirement("MATH", 2, 1)
    ]

    result = solve_with_stats(problem)

    assert result.timetable is None
    assert result.stats.nodes_explored >= 0
