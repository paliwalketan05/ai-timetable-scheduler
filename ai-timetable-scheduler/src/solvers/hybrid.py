
"""Hybrid solver combining heuristic backtracking and Simulated Annealing."""

from dataclasses import dataclass

from src.evaluation.metrics import calculate_soft_penalty
from src.evaluation.validator import validate_timetable
from src.models.entities import SchedulingProblem
from src.models.schedule import Timetable
from src.solvers.heuristic_backtracking import solve_with_stats as heuristic_solve
from src.solvers.simulated_annealing import solve_with_stats as annealing_solve


@dataclass
class HybridStats:
    backtracking_nodes: int = 0
    backtracking_backtracks: int = 0
    annealing_iterations: int = 0
    annealing_accepted_moves: int = 0


@dataclass
class HybridResult:
    timetable: Timetable | None
    stats: HybridStats


def solve_with_stats(
    problem: SchedulingProblem,
    max_steps: int = 2_000,
    seed: int | None = None,
) -> HybridResult:
    """Find a valid timetable, then attempt to improve its soft score."""
    first = heuristic_solve(problem)
    stats = HybridStats(
        backtracking_nodes=first.stats.nodes_explored,
        backtracking_backtracks=first.stats.backtracks,
    )

    if first.timetable is None:
        return HybridResult(None, stats)

    best = first.timetable
    if validate_timetable(best, problem):
        return HybridResult(None, stats)

    annealed = annealing_solve(
        problem,
        max_steps=max_steps,
        max_restarts=0,
        seed=seed,
        initial_timetable=best,
    )

    stats.annealing_iterations = annealed.stats.iterations
    stats.annealing_accepted_moves = annealed.stats.accepted_moves

    candidate = annealed.timetable
    if candidate is not None and not validate_timetable(candidate, problem):
        best_score = calculate_soft_penalty(best)["total"]
        candidate_score = calculate_soft_penalty(candidate)["total"]

        if candidate_score < best_score:
            best = candidate

    return HybridResult(best, stats)


def solve(problem: SchedulingProblem) -> Timetable | None:
    """Return the hybrid solver's best valid timetable."""
    return solve_with_stats(problem).timetable
