
"""Run and compare multiple timetable solvers."""

from dataclasses import dataclass
from typing import Callable

from src.evaluation.runner import SolverResult, evaluate_solver
from src.models.entities import SchedulingProblem
from src.models.schedule import Timetable
from src.solvers.backtracking import solve as basic_backtracking
from src.solvers.heuristic_backtracking import solve_with_stats as heuristic_solve
from src.solvers.min_conflicts import solve_with_stats as min_conflicts_solve
from src.solvers.simulated_annealing import solve_with_stats as annealing_solve


Solver = Callable[[SchedulingProblem], Timetable | None]
Statistics = dict[str, int | float]


@dataclass
class ExperimentRun:
    """One measured run of a solver."""

    solver_name: str
    result: SolverResult
    statistics: Statistics


@dataclass
class SolverSummary:
    """Aggregated results for repeated solver runs."""

    solver_name: str
    runs: list[ExperimentRun]

    @property
    def success_count(self) -> int:
        return sum(run.result.success for run in self.runs)

    @property
    def success_rate(self) -> float:
        if not self.runs:
            return 0.0
        return self.success_count / len(self.runs)

    @property
    def average_runtime_seconds(self) -> float:
        if not self.runs:
            return 0.0
        return sum(
            run.result.runtime_seconds for run in self.runs
        ) / len(self.runs)

    @property
    def best_result(self) -> SolverResult | None:
        valid = [
            run.result for run in self.runs
            if run.result.success
        ]
        if not valid:
            return None
        return min(
            valid,
            key=lambda result: (
                result.total_soft_penalty
                if result.total_soft_penalty is not None
                else float("inf")
            ),
        )


def _run_with_statistics(
    solver_name: str,
    seed: int | None = None,
) -> tuple[Solver, Callable[[], Statistics]]:
    """Adapt a solver to the common interface and expose its statistics."""
    statistics: Statistics = {}

    if solver_name == "basic_backtracking":
        return basic_backtracking, lambda: {}

    if solver_name == "heuristic_backtracking":
        def run(problem: SchedulingProblem) -> Timetable | None:
            outcome = heuristic_solve(problem)
            statistics.clear()
            statistics.update({
                "nodes_explored": outcome.stats.nodes_explored,
                "backtracks": outcome.stats.backtracks,
            })
            return outcome.timetable

    elif solver_name == "min_conflicts":
        def run(problem: SchedulingProblem) -> Timetable | None:
            outcome = min_conflicts_solve(problem, seed=seed)
            statistics.clear()
            statistics.update({
                "iterations": outcome.stats.iterations,
                "restarts": outcome.stats.restarts,
                "plateau_escapes": outcome.stats.plateau_escapes,
            })
            return outcome.timetable

    elif solver_name == "simulated_annealing":
        def run(problem: SchedulingProblem) -> Timetable | None:
            outcome = annealing_solve(problem, seed=seed)
            statistics.clear()
            statistics.update({
                "iterations": outcome.stats.iterations,
                "accepted_moves": outcome.stats.accepted_moves,
                "worse_moves_accepted": outcome.stats.worse_moves_accepted,
                "restarts": outcome.stats.restarts,
            })
            return outcome.timetable

    else:
        raise ValueError(f"Unknown solver: {solver_name}")

    return run, lambda: dict(statistics)


def run_experiment(
    problem: SchedulingProblem,
    solver_names: list[str] | None = None,
    repetitions: int = 1,
    weights: dict[str, int] | None = None,
    seed: int | None = None,
) -> dict[str, SolverSummary]:
    """Compare solvers on the same problem over repeated runs.

    When a seed is provided, randomized solvers receive a reproducible
    sequence of seeds, one per repetition.
    """
    if repetitions < 1:
        raise ValueError("repetitions must be at least 1")

    available = [
        "basic_backtracking",
        "heuristic_backtracking",
        "min_conflicts",
        "simulated_annealing",
    ]
    selected = solver_names or available

    unknown = set(selected) - set(available)
    if unknown:
        raise ValueError(f"Unknown solvers: {sorted(unknown)}")

    summaries: dict[str, SolverSummary] = {}

    for solver_name in selected:
        runs = []

        for repetition in range(repetitions):
            run_seed = (
                seed + repetition
                if seed is not None
                else None
            )
            solver, get_statistics = _run_with_statistics(
                solver_name,
                seed=run_seed,
            )
            result = evaluate_solver(solver, problem, weights)

            runs.append(
                ExperimentRun(
                    solver_name=solver_name,
                    result=result,
                    statistics=get_statistics(),
                )
            )

        summaries[solver_name] = SolverSummary(solver_name, runs)

    return summaries


def recommend_timetable(
    summaries: dict[str, SolverSummary],
) -> tuple[str, Timetable] | None:
    """Return the lowest-penalty valid timetable found across all runs."""
    candidates = []

    for solver_name, summary in summaries.items():
        for run in summary.runs:
            result = run.result
            if result.success and result.timetable is not None:
                penalty = result.total_soft_penalty
                candidates.append((
                    penalty if penalty is not None else float("inf"),
                    solver_name,
                    result.timetable,
                ))

    if not candidates:
        return None

    _, solver_name, timetable = min(
        candidates,
        key=lambda item: item[0],
    )
    return solver_name, timetable
