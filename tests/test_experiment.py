
from src.evaluation.experiment import (
    recommend_timetable,
    run_experiment,
)
from src.models.entities import (
    SchedulingProblem,
    Subject,
    SubjectRequirement,
    Teacher,
    StudentGroup,
    Room,
    TimeStructure,
)


def make_problem():
    return SchedulingProblem(
        subjects=[Subject("MATH", "Mathematics")],
        teachers=[
            Teacher("T1", "Teacher One", ["MATH"], maximum_weekly_load=2)
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


def test_experiment_runs_selected_solver():
    summaries = run_experiment(
        make_problem(),
        solver_names=["heuristic_backtracking"],
        repetitions=2,
    )

    summary = summaries["heuristic_backtracking"]
    assert len(summary.runs) == 2
    assert summary.success_count == 2
    assert summary.success_rate == 1.0
    assert summary.average_runtime_seconds >= 0
    assert "nodes_explored" in summary.runs[0].statistics


def test_recommendation_returns_valid_timetable():
    summaries = run_experiment(
        make_problem(),
        solver_names=["basic_backtracking", "heuristic_backtracking"],
    )

    recommendation = recommend_timetable(summaries)

    assert recommendation is not None
    solver_name, timetable = recommendation
    assert solver_name in {"basic_backtracking", "heuristic_backtracking"}
    assert len(timetable.sessions) == 2


def test_experiment_rejects_unknown_solver():
    try:
        run_experiment(make_problem(), solver_names=["not_a_solver"])
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for unknown solver")


def test_experiment_rejects_zero_repetitions():
    try:
        run_experiment(make_problem(), repetitions=0)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for zero repetitions")


def test_randomized_solver_experiment_accepts_seed():
    summaries = run_experiment(
        make_problem(),
        solver_names=["simulated_annealing"],
        repetitions=2,
        seed=42,
    )

    summary = summaries["simulated_annealing"]
    assert len(summary.runs) == 2
    assert all(
        "iterations" in run.statistics
        for run in summary.runs
    )
