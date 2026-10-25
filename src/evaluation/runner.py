"""Run a timetable solver and evaluate its result."""
from dataclasses import dataclass
from time import perf_counter
from typing import Callable
from src.evaluation.metrics import calculate_soft_penalty
from src.evaluation.validator import validate_timetable
from src.models.entities import SchedulingProblem
from src.models.schedule import Timetable

Solver=Callable[[SchedulingProblem],Timetable | None]

@dataclass
class SolverResult:
    """Evaluation results for one solver run."""

    success: bool
    runtime_seconds: float
    hard_violations: list[str]
    soft_penalties:dict[str,int]| None
    timetable: Timetable | None

    @property
    def total_soft_penalty(self)->int | None:
        """Return the weighted penalty, if a valid timetable was found."""
        if self.soft_penalties is None:
            return None
        return self.soft_penalties["total"]

def evaluate_solver(
        solver: Solver,
        problem: SchedulingProblem,
        weights:dict[str,int] | None= None,
)->SolverResult:
    """Run a solver, validate its timetable, and score valid results."""
    start=perf_counter()
    timetable=solver(problem)
    runtime_seconds=perf_counter()-start

    if timetable is None:
        return SolverResult(
            success=False,
            runtime_seconds=runtime_seconds,
            hard_violations=["Solver did not find a timetable."],
            soft_penalties=None,
            timetable=None,
        )

    violations=validate_timetable(timetable,problem)

    if violations:
        return SolverResult(
            success=False,
            runtime_seconds=runtime_seconds,
            hard_violations=violations,
            soft_penalties=None,
            timetable=timetable,
        )
    return SolverResult(
        success=True,
        runtime_seconds=runtime_seconds,
        hard_violations=[],
        soft_penalties=calculate_soft_penalty(timetable,weights),
        timetable=timetable,
    )