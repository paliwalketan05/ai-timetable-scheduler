"""Build candidate assignments for each scheduling session."""

from src.csp.sessions import SchedulingSession
from src.models.entities import SchedulingProblem
from src.models.schedule import Assignment

def _slot_key(day: str, period: int) -> str:
    """Return the canonical key for a day and period."""
    return f"{day}_P{period}"

def _teacher_is_available(
    teacher,
    day: str,
    start_period: int,
    duration: int,
) -> bool:
    unavailable = set(teacher.unavailable_slots)

    for period in range(start_period, start_period + duration):
        if _slot_key(day, period) in unavailable:
            return False

    return True


def _session_fits_day(
    problem: SchedulingProblem,
    group_id: str,
    day: str,
    start_period: int,
    duration: int,
) -> bool:
    """Check bounds, breaks, and the class's lunch periods."""
    settings = problem.time_structure
    final_period = start_period + duration - 1

    if start_period < 1 or final_period > settings.periods_per_day:
        return False

    occupied = set(range(start_period, final_period + 1))

    if occupied.intersection(settings.break_periods):
        return False

    group = next(
        (item for item in problem.student_groups if item.id == group_id),
        None,
    )

    if group is None:
        return False

    if occupied.intersection(group.lunch_break_periods):
        return False

    return True


def generate_domains(
        problem: SchedulingProblem,
        sessions: list[SchedulingSession],
) -> dict[str, list[Assignment]]:
    """Generate candidate assignments for each session.

    Candidates combine qualified teachers, valid day/period placements,
    and rooms with sufficient capacity and a compatible room type.

    This function does not resolve conflicts between different sessions.
    Those are enforced by the constraint engine and solver.
    """
    subjects = {subject.id: subject for subject in problem.subjects}
    groups = {group.id: group for group in problem.student_groups}

    domains: dict[str, list[Assignment]] = {}

    for session in sessions:
        candidates=[]

        subject= subjects.get(session.subject_id)
        group= groups.get(session.group_id)

        if subject is None or group is None:
            domains[session.id]=[]
            continue

        required_room_type=(
            "lab" if subject.subject_type.strip().lower()=="lab"
            else "classroom"
        )

        eligible_teachers=[
            teacher
            for teacher in problem.teachers
            if session.subject_id in teacher.subjects_can_teach
        ]
        compatible_rooms=[
            room
            for room in problem.rooms
            if room.capacity >= group.strength
            and room.room_type.strip().lower()== required_room_type
        ]


        for day in problem.time_structure.working_days:
            for start_period in range(
                1, problem.time_structure.periods_per_day + 1
            ):
                if not _session_fits_day(
                    problem,
                    session.group_id,
                    day,
                    start_period,
                    session.duration_slots,
                ):
                    continue

                for teacher in eligible_teachers:
                    if not _teacher_is_available(
                        teacher,
                        day,
                        start_period,
                        session.duration_slots,
                    ):
                        continue

                    for room in compatible_rooms:
                        candidates.append(
                            Assignment(
                                session_id=session.id,
                                teacher_id=teacher.id,
                                day=day,
                                start_period=start_period,
                                room_id=room.id,
                            )
                        )

        domains[session.id]=candidates
    return domains