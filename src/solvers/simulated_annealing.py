"""Simulated annealing optimization solver."""

"""Simulated Annealing solver for timetable optimization."""

from dataclasses import dataclass
import math
import random

from src.csp.domains import generate_domains
from src.csp.sessions import expand_sessions
from src.evaluation.metrics import calculate_soft_penalty
from src.evaluation.validator import validate_timetable
from src.models.entities import SchedulingProblem
from src.models.schedule import ScheduledSession, Timetable
from src.solvers.heuristics import make_scheduled_session


@dataclass
class AnnealingStats:
    iterations: int = 0
    accepted_moves: int = 0
    worse_moves_accepted: int = 0
    restarts: int = 0


@dataclass
class AnnealingResult:
    timetable: Timetable | None
    stats: AnnealingStats


def _soft_score(timetable: Timetable) -> int:
    return calculate_soft_penalty(timetable)["total"]


def solve_with_stats(
    problem: SchedulingProblem,
    max_steps: int = 5_000,
    initial_temperature: float = 10.0,
    cooling_rate: float = 0.995,
    min_temperature: float = 0.01,
    max_restarts: int = 3,
    seed: int | None = None,
) -> AnnealingResult:
    """Search for a valid timetable with progressively cooler moves."""
    if max_steps < 1:
        raise ValueError("max_steps must be positive")
    if initial_temperature <= 0 or min_temperature <= 0:
        raise ValueError("Temperatures must be positive")
    if not 0 < cooling_rate < 1:
        raise ValueError("cooling_rate must be between 0 and 1")
    if max_restarts < 0:
        raise ValueError("max_restarts cannot be negative")

    rng = random.Random(seed)
    stats = AnnealingStats()
    sessions = expand_sessions(problem)
    domains = generate_domains(problem, sessions)

    if not sessions:
        timetable = Timetable(sessions=[])
        if not validate_timetable(timetable, problem):
            return AnnealingResult(timetable, stats)
        return AnnealingResult(None, stats)

    if any(not domains[session.id] for session in sessions):
        return AnnealingResult(None, stats)

    best_valid: Timetable | None = None
    best_valid_score = math.inf

    for restart in range(max_restarts + 1):
        if restart > 0:
            stats.restarts += 1

        current_sessions = [
            make_scheduled_session(session, rng.choice(domains[session.id]))
            for session in sessions
        ]
        current = Timetable(sessions=current_sessions)
        temperature = initial_temperature

        current_violations = validate_timetable(current, problem)
        if not current_violations:
            score = _soft_score(current)
            if score < best_valid_score:
                best_valid = current
                best_valid_score = score

        for _ in range(max_steps):
            if temperature <= min_temperature:
                break

            stats.iterations += 1
            index = rng.randrange(len(sessions))
            session = sessions[index]
            current_item = current.sessions[index]
            alternatives = [
                assignment
                for assignment in domains[session.id]
                if assignment != current_item.assignment
            ]

            if not alternatives:
                temperature *= cooling_rate
                continue

            replacement = make_scheduled_session(
                session,
                rng.choice(alternatives),
            )
            candidate_sessions = current.sessions.copy()
            candidate_sessions[index] = replacement
            candidate = Timetable(sessions=candidate_sessions)

            candidate_violations = validate_timetable(candidate, problem)
            current_violations = validate_timetable(current, problem)

            # A candidate that is valid is always preferred over an invalid
            # current state. Otherwise compare the number of hard violations.
            current_hard_score = len(current_violations)
            candidate_hard_score = len(candidate_violations)

            if candidate_hard_score == 0:
                candidate_score = _soft_score(candidate)
                if candidate_score < best_valid_score:
                    best_valid = candidate
                    best_valid_score = candidate_score

            current_score = (
                current_hard_score * 1_000_000
                + (_soft_score(current) if current_hard_score == 0 else 0)
            )
            candidate_score = (
                candidate_hard_score * 1_000_000
                + (_soft_score(candidate) if candidate_hard_score == 0 else 0)
            )
            delta = candidate_score - current_score

            accept = delta <= 0
            if not accept and temperature > 0:
                accept = rng.random() < math.exp(-delta / temperature)

            if accept:
                current = candidate
                stats.accepted_moves += 1
                if delta > 0:
                    stats.worse_moves_accepted += 1

            temperature *= cooling_rate

    return AnnealingResult(best_valid, stats)


def solve(problem: SchedulingProblem) -> Timetable | None:
    """Return the best valid timetable found, or None."""
    return solve_with_stats(problem).timetable
