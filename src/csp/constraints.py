from src.models.schedule import ScheduledSession
from src.models.entities import SchedulingProblem, StudentGroup, Subject, Teacher, Room

def _sessions_overlap(
    session_a: ScheduledSession,
    session_b: ScheduledSession,
) -> bool:
    if session_a.assignment.day != session_b.assignment.day:
        return False

    start_a = session_a.assignment.start_period
    end_a = start_a + session_a.duration_slots - 1

    start_b = session_b.assignment.start_period
    end_b = start_b + session_b.duration_slots - 1

    return start_a <= end_b and start_b <= end_a

def has_teacher_conflict(
    candidate: ScheduledSession,
    scheduled_sessions: list[ScheduledSession],
) -> bool:
    for session in scheduled_sessions:
        if session.session_id == candidate.session_id:
            continue

        if (
            session.assignment.teacher_id == candidate.assignment.teacher_id
            and _sessions_overlap(candidate, session)
        ):
            return True

    return False


def has_group_conflict(
    candidate: ScheduledSession,
    scheduled_sessions: list[ScheduledSession],
) -> bool:
    for session in scheduled_sessions:
        if session.session_id == candidate.session_id:
            continue

        if (
            session.group_id == candidate.group_id
            and _sessions_overlap(candidate, session)
        ):
            return True

    return False


def has_room_conflict(
    candidate: ScheduledSession,
    scheduled_sessions: list[ScheduledSession],
) -> bool:
    for session in scheduled_sessions:
        if session.session_id == candidate.session_id:
            continue

        if (
            session.assignment.room_id == candidate.assignment.room_id
            and _sessions_overlap(candidate, session)
        ):
            return True

    return False

def has_room_capacity_violation(
    candidate: ScheduledSession,
    problem: SchedulingProblem,
) -> bool:
    group = next(
        (group for group in problem.student_groups if group.id == candidate.group_id),
        None,
    )
    room = next(
        (room for room in problem.rooms if room.id == candidate.assignment.room_id),
        None,
    )

    if group is None or room is None:
        return True

    return room.capacity < group.strength


def has_room_type_violation(
    candidate: ScheduledSession,
    problem: SchedulingProblem,
) -> bool:
    subject = next(
        (subject for subject in problem.subjects if subject.id == candidate.subject_id),
        None,
    )
    room = next(
        (room for room in problem.rooms if room.id == candidate.assignment.room_id),
        None,
    )

    if subject is None or room is None:
        return True

    required_type = (
        "lab" if subject.subject_type.strip().lower() == "lab"
        else "classroom"
    )

    return room.room_type.strip().lower() != required_type


def has_teacher_availability_violation(
    candidate: ScheduledSession,
    problem: SchedulingProblem,
) -> bool:
    teacher = next(
        (
            teacher for teacher in problem.teachers
            if teacher.id == candidate.assignment.teacher_id
        ),
        None,
    )

    if teacher is None:
        return True

    unavailable = set(teacher.unavailable_slots)

    for period in range(
        candidate.assignment.start_period,
        candidate.assignment.start_period + candidate.duration_slots,
    ):
        if f"{candidate.assignment.day}_P{period}" in unavailable:
            return True

    return False