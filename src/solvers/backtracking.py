from dataclasses import dataclass
from src.csp.sessions import expand_sessions
from src.csp.domains import generate_domains
from src.evaluation.validator import validate_timetable
from src.csp.sessions import SchedulingSession
from src.csp.constraints import (
    has_teacher_conflict,
    has_group_conflict,
    has_room_conflict,
    has_room_capacity_violation,
    has_room_type_violation,
    has_teacher_availability_violation,
)
from src.models.entities import SchedulingProblem
from src.models.schedule import Assignment, ScheduledSession, Timetable


def _make_scheduled_session(
    session: SchedulingSession,
    assignment: Assignment,
) -> ScheduledSession:
    return ScheduledSession(
        session_id=session.id,
        group_id=session.group_id,
        subject_id=session.subject_id,
        duration_slots=session.duration_slots,
        assignment=assignment,
    )


def _is_consistent(
    candidate: ScheduledSession,
    scheduled_sessions: list[ScheduledSession],
    problem: SchedulingProblem,
) -> bool:
    if has_teacher_conflict(candidate, scheduled_sessions):
        return False

    if has_group_conflict(candidate, scheduled_sessions):
        return False

    if has_room_conflict(candidate, scheduled_sessions):
        return False

    if has_room_capacity_violation(candidate, problem):
        return False

    if has_room_type_violation(candidate, problem):
        return False

    if has_teacher_availability_violation(candidate, problem):
        return False

    if _exceeds_teacher_workload(candidate, scheduled_sessions, problem):
        return False

    return True


def _exceeds_teacher_workload(
    candidate: ScheduledSession,
    scheduled_sessions: list[ScheduledSession],
    problem: SchedulingProblem,
) -> bool:
    teacher = next(
        (
            teacher
            for teacher in problem.teachers
            if teacher.id == candidate.assignment.teacher_id
        ),
        None,
    )

    if teacher is None:
        return True

    current_load = sum(
        session.duration_slots
        for session in scheduled_sessions
        if session.assignment.teacher_id == teacher.id
    )

    proposed_load = current_load + candidate.duration_slots

    return proposed_load > teacher.maximum_weekly_load

@dataclass
class BacktrackingStats:
    nodes_explored: int = 0
    backtracks: int = 0


@dataclass
class BacktrackingResult:
    timetable: Timetable | None
    stats: BacktrackingStats

def _backtrack(
    sessions: list[SchedulingSession],
    domains: dict[str, list[Assignment]],
    problem: SchedulingProblem,
    scheduled: list[ScheduledSession],
    stats:BacktrackingStats,
) -> list[ScheduledSession] | None:
    if len(scheduled) == len(sessions):
        return scheduled.copy()

    scheduled_ids = {session.session_id for session in scheduled}
    stats.nodes_explored += 1
    session = next(
        session for session in sessions
        if session.id not in scheduled_ids
    )

    for assignment in domains[session.id]:
        candidate = _make_scheduled_session(session, assignment)

        if not _is_consistent(candidate, scheduled, problem):
            continue

        scheduled.append(candidate)

        result = _backtrack(
            sessions=sessions,
            domains=domains,
            problem=problem,
            scheduled=scheduled,
            stats=stats,
        )

        if result is not None:
            return result

        stats.backtracks += 1
        scheduled.pop()

    return None


def solve_with_stats(problem: SchedulingProblem) -> BacktrackingResult:
    """Solve the problem and return search statistics."""
    stats = BacktrackingStats()
    sessions = expand_sessions(problem)
    domains = generate_domains(problem, sessions)

    if any(not domain for domain in domains.values()):
        return BacktrackingResult(None, stats)

    solution = _backtrack(
        sessions=sessions,
        domains=domains,
        problem=problem,
        scheduled=[],
        stats=stats,
    )

    if solution is None:
        return BacktrackingResult(None, stats)

    timetable = Timetable(sessions=solution)
    violations = validate_timetable(timetable, problem)

    if violations:
        return BacktrackingResult(None, stats)

    return BacktrackingResult(timetable, stats)


def solve(problem: SchedulingProblem) -> Timetable | None:
    """Return only the timetable for compatibility with existing callers."""
    return solve_with_stats(problem).timetable