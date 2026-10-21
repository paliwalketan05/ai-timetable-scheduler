
"""Min-Conflicts solver with random restarts and plateau escape."""

from dataclasses import dataclass
import random

from src.csp.constraints import (
    has_group_conflict,
    has_room_conflict,
    has_teacher_conflict,
)
from src.csp.domains import generate_domains
from src.csp.sessions import SchedulingSession, expand_sessions
from src.evaluation.validator import validate_timetable
from src.models.entities import SchedulingProblem
from src.models.schedule import Assignment, ScheduledSession, Timetable
from src.solvers.heuristics import make_scheduled_session


@dataclass
class MinConflictsStats:
    iterations: int = 0
    restarts: int = 0
    plateau_escapes: int = 0


@dataclass
class MinConflictsResult:
    timetable: Timetable | None
    stats: MinConflictsStats


def _teacher_load(
    teacher_id: str,
    assignments: list[ScheduledSession],
) -> int:
    return sum(
        item.duration_slots
        for item in assignments
        if item.assignment.teacher_id == teacher_id
    )


def _conflict_count(
    candidate: ScheduledSession,
    assignments: list[ScheduledSession],
    problem: SchedulingProblem,
) -> int:
    """Score conflicts introduced by one candidate assignment."""
    others = [
        item for item in assignments
        if item.session_id != candidate.session_id
    ]

    conflicts = 0

    if has_teacher_conflict(candidate, others):
        conflicts += sum(
            1 for item in others
            if item.assignment.teacher_id == candidate.assignment.teacher_id
            and _overlap(candidate, item)
        )

    if has_group_conflict(candidate, others):
        conflicts += sum(
            1 for item in others
            if item.group_id == candidate.group_id
            and _overlap(candidate, item)
        )

    if has_room_conflict(candidate, others):
        conflicts += sum(
            1 for item in others
            if item.assignment.room_id == candidate.assignment.room_id
            and _overlap(candidate, item)
        )

    teacher = next(
        (
            item for item in problem.teachers
            if item.id == candidate.assignment.teacher_id
        ),
        None,
    )

    if teacher is None:
        conflicts += 1
    else:
        load = _teacher_load(teacher.id, others) + candidate.duration_slots
        if load > teacher.maximum_weekly_load:
            conflicts += 1

    return conflicts


def _overlap(
    first: ScheduledSession,
    second: ScheduledSession,
) -> bool:
    if first.assignment.day != second.assignment.day:
        return False

    first_start = first.assignment.start_period
    first_end = first_start + first.duration_slots - 1
    second_start = second.assignment.start_period
    second_end = second_start + second.duration_slots - 1

    return first_start <= second_end and second_start <= first_end


def _total_conflicts(
    assignments: list[ScheduledSession],
    problem: SchedulingProblem,
) -> int:
    """Count each overlapping pair once, plus teacher workload violations."""
    conflicts = 0

    for index, candidate in enumerate(assignments):
        for other in assignments[index + 1:]:
            if (
                has_teacher_conflict(candidate, [other])
                or has_group_conflict(candidate, [other])
                or has_room_conflict(candidate, [other])
            ):
                conflicts += sum((
                    has_teacher_conflict(candidate, [other]),
                    has_group_conflict(candidate, [other]),
                    has_room_conflict(candidate, [other]),
                ))

    for teacher in problem.teachers:
        load = _teacher_load(teacher.id, assignments)
        if load > teacher.maximum_weekly_load:
            conflicts += 1

    return conflicts


def _make_initial_assignment(
    sessions: list[SchedulingSession],
    domains: dict[str, list[Assignment]],
    rng: random.Random,
) -> list[ScheduledSession] | None:
    """Choose a random domain value for every session."""
    assignments = []

    for session in sessions:
        if not domains[session.id]:
            return None

        assignments.append(
            make_scheduled_session(
                session,
                rng.choice(domains[session.id]),
            )
        )

    return assignments


def solve_with_stats(
    problem: SchedulingProblem,
    max_steps: int = 2_000,
    max_restarts: int = 20,
    plateau_limit: int = 100,
    seed: int | None = None,
) -> MinConflictsResult:
    """Run Min-Conflicts with random restarts and plateau escapes."""
    if max_steps < 1 or max_restarts < 0 or plateau_limit < 1:
        raise ValueError(
            "max_steps and plateau_limit must be positive; "
            "max_restarts cannot be negative"
        )

    rng = random.Random(seed)
    stats = MinConflictsStats()
    sessions = expand_sessions(problem)
    domains = generate_domains(problem, sessions)

    if any(not domains[session.id] for session in sessions):
        return MinConflictsResult(None, stats)

    if not sessions:
        timetable = Timetable(sessions=[])
        if not validate_timetable(timetable, problem):
            return MinConflictsResult(timetable, stats)
        return MinConflictsResult(None, stats)

    for restart in range(max_restarts + 1):
        if restart:
            stats.restarts += 1

        current = _make_initial_assignment(sessions, domains, rng)
        if current is None:
            return MinConflictsResult(None, stats)

        best_score = _total_conflicts(current, problem)
        plateau_steps = 0

        for _ in range(max_steps):
            stats.iterations += 1

            violations = [
                item for item in current
                if _conflict_count(item, current, problem) > 0
            ]

            if not violations and _total_conflicts(current, problem) == 0:
                timetable = Timetable(sessions=current.copy())
                if not validate_timetable(timetable, problem):
                    return MinConflictsResult(timetable, stats)

            if violations:
                selected = rng.choice(violations)
            else:
                selected = rng.choice(current)

            session = next(
                item for item in sessions
                if item.id == selected.session_id
            )
            others = [
                item for item in current
                if item.session_id != session.id
            ]

            scored = [
                (
                    _conflict_count(
                        make_scheduled_session(session, assignment),
                        others,
                        problem,
                    ),
                    assignment,
                )
                for assignment in domains[session.id]
            ]

            minimum = min(score for score, _ in scored)
            choices = [
                assignment for score, assignment in scored
                if score == minimum
            ]
            chosen = rng.choice(choices)

            replacement = make_scheduled_session(session, chosen)
            current = [
                replacement if item.session_id == session.id else item
                for item in current
            ]

            total_score = _total_conflicts(current, problem)

            if total_score < best_score:
                best_score = total_score
                plateau_steps = 0
            else:
                plateau_steps += 1

            if plateau_steps >= plateau_limit:
                stats.plateau_escapes += 1

                # Perturb a random session to explore a different state.
                target = rng.choice(sessions)
                old_assignment = next(
                    item.assignment for item in current
                    if item.session_id == target.id
                )
                alternatives = [
                    assignment for assignment in domains[target.id]
                    if assignment != old_assignment
                ]

                if alternatives:
                    replacement = make_scheduled_session(
                        target,
                        rng.choice(alternatives),
                    )
                    current = [
                        replacement if item.session_id == target.id else item
                        for item in current
                    ]

                best_score = _total_conflicts(current, problem)
                plateau_steps = 0

    return MinConflictsResult(None, stats)


def solve(problem: SchedulingProblem) -> Timetable | None:
    """Return only the timetable for compatibility with other solvers."""
    return solve_with_stats(problem).timetable
