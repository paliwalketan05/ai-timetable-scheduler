
"""Backtracking solver using MRV, Degree, and Forward Checking."""

from dataclasses import dataclass

from src.csp.sessions import expand_sessions, SchedulingSession
from src.evaluation.validator import validate_timetable
from src.models.entities import SchedulingProblem
from src.models.schedule import Assignment, ScheduledSession, Timetable
from src.solvers.heuristics import (
    forward_check,
    initial_domains,
    is_consistent,
    make_scheduled_session,
    select_mrv_degree_session,
)


@dataclass
class SearchStats:
    """Search effort recorded by the heuristic solver."""

    nodes_explored: int = 0
    backtracks: int = 0


@dataclass
class HeuristicSolveResult:
    """Solution and search statistics from one heuristic solve."""

    timetable: Timetable | None
    stats: SearchStats


def _search(
    sessions: list[SchedulingSession],
    domains: dict[str, list[Assignment]],
    problem: SchedulingProblem,
    scheduled: list[ScheduledSession],
    stats: SearchStats,
) -> list[ScheduledSession] | None:
    if len(scheduled) == len(sessions):
        return scheduled.copy()

    session = select_mrv_degree_session(sessions, domains, scheduled)

    for assignment in domains[session.id]:
        stats.nodes_explored += 1
        candidate = make_scheduled_session(session, assignment)

        if not is_consistent(candidate, scheduled, problem):
            continue

        scheduled.append(candidate)

        remaining_domains = forward_check(
            sessions,
            domains,
            scheduled,
            problem,
        )

        if remaining_domains is not None:
            result = _search(
                sessions,
                remaining_domains,
                problem,
                scheduled,
                stats,
            )

            if result is not None:
                return result

        scheduled.pop()
        stats.backtracks += 1

    return None


def solve_with_stats(problem: SchedulingProblem) -> HeuristicSolveResult:
    """Solve a problem and return the timetable plus search statistics."""
    sessions = expand_sessions(problem)
    domains = initial_domains(problem, sessions)
    stats = SearchStats()

    if any(not domain for domain in domains.values()):
        return HeuristicSolveResult(None, stats)

    solution = _search(
        sessions=sessions,
        domains=domains,
        problem=problem,
        scheduled=[],
        stats=stats,
    )

    if solution is None:
        return HeuristicSolveResult(None, stats)

    timetable = Timetable(sessions=solution)

    if validate_timetable(timetable, problem):
        return HeuristicSolveResult(None, stats)

    return HeuristicSolveResult(timetable, stats)


def solve(problem: SchedulingProblem) -> Timetable | None:
    """Compatibility interface returning only the timetable."""
    return solve_with_stats(problem).timetable
