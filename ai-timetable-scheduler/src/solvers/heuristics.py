
"""Shared search heuristics, including MRV, Degree, and forward checking."""

from src.csp.constraints import (
    has_group_conflict,
    has_room_conflict,
    has_teacher_conflict,
)
from src.csp.domains import generate_domains
from src.csp.sessions import SchedulingSession
from src.models.entities import SchedulingProblem
from src.models.schedule import Assignment, ScheduledSession


def make_scheduled_session(
    session: SchedulingSession,
    assignment: Assignment,
) -> ScheduledSession:
    """Convert a CSP session and candidate into a scheduled session."""
    return ScheduledSession(
        session_id=session.id,
        group_id=session.group_id,
        subject_id=session.subject_id,
        duration_slots=session.duration_slots,
        assignment=assignment,
    )


def is_consistent(
    candidate: ScheduledSession,
    scheduled: list[ScheduledSession],
    problem: SchedulingProblem,
) -> bool:
    """Return whether a candidate conflicts with existing assignments."""
    if has_teacher_conflict(candidate, scheduled):
        return False
    if has_group_conflict(candidate, scheduled):
        return False
    if has_room_conflict(candidate, scheduled):
        return False

    # Domain generation handles these static restrictions, but keep
    # this check for assignments supplied from any other source.
    from src.csp.constraints import (
        has_room_capacity_violation,
        has_room_type_violation,
        has_teacher_availability_violation,
    )

    if has_room_capacity_violation(candidate, problem):
        return False
    if has_room_type_violation(candidate, problem):
        return False
    if has_teacher_availability_violation(candidate, problem):
        return False

    teacher = next(
        (
            item for item in problem.teachers
            if item.id == candidate.assignment.teacher_id
        ),
        None,
    )
    if teacher is None:
        return False

    current_load = sum(
        item.duration_slots
        for item in scheduled
        if item.assignment.teacher_id == teacher.id
    )
    return current_load + candidate.duration_slots <= teacher.maximum_weekly_load


def select_mrv_session(
    sessions: list[SchedulingSession],
    domains: dict[str, list[Assignment]],
    scheduled: list[ScheduledSession],
) -> SchedulingSession:
    """Choose the unscheduled session with the smallest remaining domain."""
    scheduled_ids = {item.session_id for item in scheduled}
    remaining = [item for item in sessions if item.id not in scheduled_ids]

    if not remaining:
        raise ValueError("No unscheduled sessions remain")

    return min(remaining, key=lambda item: (len(domains[item.id]), item.id))


def degree_score(
    session: SchedulingSession,
    remaining_sessions: list[SchedulingSession],
) -> int:
    """Estimate how many other sessions share a group or subject."""
    score = 0

    for other in remaining_sessions:
        if other.id == session.id:
            continue

        # Sessions for the same group can never overlap.
        if other.group_id == session.group_id:
            score += 1
        # Sessions with the same subject may compete for the same teachers.
        elif other.subject_id == session.subject_id:
            score += 1

    return score


def select_mrv_degree_session(
    sessions: list[SchedulingSession],
    domains: dict[str, list[Assignment]],
    scheduled: list[ScheduledSession],
) -> SchedulingSession:
    """Use MRV first, then Degree to break ties."""
    scheduled_ids = {item.session_id for item in scheduled}
    remaining = [item for item in sessions if item.id not in scheduled_ids]

    if not remaining:
        raise ValueError("No unscheduled sessions remain")

    smallest_domain = min(len(domains[item.id]) for item in remaining)
    tied = [
        item for item in remaining
        if len(domains[item.id]) == smallest_domain
    ]

    return max(
        tied,
        key=lambda item: (
            degree_score(item, remaining),
            item.id,
        ),
    )


def forward_check(
    sessions: list[SchedulingSession],
    domains: dict[str, list[Assignment]],
    scheduled: list[ScheduledSession],
    problem: SchedulingProblem,
) -> dict[str, list[Assignment]] | None:
    """Filter remaining domains; return None if any domain becomes empty."""
    scheduled_ids = {item.session_id for item in scheduled}
    filtered = {}

    for session in sessions:
        if session.id in scheduled_ids:
            continue

        valid_assignments = []

        for assignment in domains[session.id]:
            candidate = make_scheduled_session(session, assignment)
            if is_consistent(candidate, scheduled, problem):
                valid_assignments.append(assignment)

        if not valid_assignments:
            return None

        filtered[session.id] = valid_assignments

    return filtered


def initial_domains(
    problem: SchedulingProblem,
    sessions: list[SchedulingSession],
) -> dict[str, list[Assignment]]:
    """Build independent mutable candidate lists for a solver run."""
    return {
        session_id: list(assignments)
        for session_id, assignments
        in generate_domains(problem, sessions).items()
    }
