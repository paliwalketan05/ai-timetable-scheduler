from collections import defaultdict
from src.models.entities import SchedulingProblem
from src.models.schedule import Timetable

def _sessions_overlap(session_a, session_b):
    assignment_a = session_a.assignment
    assignment_b = session_b.assignment

    if assignment_a.day != assignment_b.day:
        return False

    start_a = assignment_a.start_period
    end_a = start_a + session_a.duration_slots - 1

    start_b = assignment_b.start_period
    end_b = start_b + session_b.duration_slots - 1

    return start_a <= end_b and start_b <= end_a

def _check_scheduling_conflicts(timetable):
    violations = []

    for i, session_a in enumerate(timetable.sessions):
        for session_b in timetable.sessions[i + 1:]:
            if not _sessions_overlap(session_a, session_b):
                continue

            if (
                session_a.assignment.teacher_id
                == session_b.assignment.teacher_id
            ):
                violations.append(
                    f"Teacher conflict: {session_a.session_id}, "
                    f"{session_b.session_id}"
                )

            if session_a.group_id == session_b.group_id:
                violations.append(
                    f"Student group conflict: {session_a.session_id}, "
                    f"{session_b.session_id}"
                )

            if (
                session_a.assignment.room_id
                == session_b.assignment.room_id
            ):
                violations.append(
                    f"Room conflict: {session_a.session_id}, "
                    f"{session_b.session_id}"
                )

    return violations
def _check_assignment_compatibility(session, problem):
    violations = []

    group = next(
        (g for g in problem.student_groups if g.id == session.group_id),
        None,
    )
    room = next(
        (r for r in problem.rooms if r.id == session.assignment.room_id),
        None,
    )
    subject = next(
        (s for s in problem.subjects if s.id == session.subject_id),
        None,
    )
    teacher = next(
        (t for t in problem.teachers if t.id == session.assignment.teacher_id),
        None,
    )

    if group is None:
        violations.append(f"Unknown student group: {session.group_id}")

    if room is None:
        violations.append(f"Unknown room: {session.assignment.room_id}")

    if subject is None:
        violations.append(f"Unknown subject: {session.subject_id}")

    if teacher is None:
        violations.append(
            f"Unknown teacher: {session.assignment.teacher_id}"
        )

    if group is not None and room is not None:
        if room.capacity < group.strength:
            violations.append(f"Room capacity violation: {session.session_id}")

    if subject is not None and room is not None:
        required_type = (
            "lab" if subject.subject_type.strip().lower() == "lab"
            else "classroom"
        )
        if room.room_type.strip().lower() != required_type:
            violations.append(f"Room type violation: {session.session_id}")

    if teacher is not None and subject is not None:
        if session.subject_id not in teacher.subjects_can_teach:
            violations.append(
                f"Teacher qualification violation: {session.session_id}"
            )

    if teacher is not None:
        unavailable = set(teacher.unavailable_slots)
        for period in range(
            session.assignment.start_period,
            session.assignment.start_period + session.duration_slots,
        ):
            slot = f"{session.assignment.day}_P{period}"
            if slot in unavailable:
                violations.append(
                    f"Teacher availability violation: {session.session_id}"
                )
                break

    return violations

def _check_timetable_integrity(timetable, problem):
    violations = []
    settings = problem.time_structure
    valid_days = set(settings.working_days)

    for session in timetable.sessions:
        assignment = session.assignment

        if session.duration_slots <= 0:
            violations.append(
                f"Invalid session duration: {session.session_id}"
            )
            continue

        start = assignment.start_period
        end = start + session.duration_slots - 1

        if assignment.day not in valid_days:
            violations.append(
                f"Invalid working day: {session.session_id}"
            )

        if start < 1 or end > settings.periods_per_day:
            violations.append(
                f"Invalid time slot: {session.session_id}"
            )

        occupied_periods = set(range(start, end + 1))

        if occupied_periods.intersection(settings.break_periods):
            violations.append(
                f"Break period violation: {session.session_id}"
            )

        if session.session_id != assignment.session_id:
            violations.append(
                f"Assignment session ID mismatch: {session.session_id}"
            )

    return violations


def validate_timetable(
    timetable: Timetable,
    problem: SchedulingProblem,
) -> list[str]:
    violations = []
    violations.extend(_check_scheduling_conflicts(timetable))
    violations.extend(_check_timetable_integrity(timetable, problem))
    for session in timetable.sessions:
        violations.extend(
            _check_assignment_compatibility(session, problem)
        )
    sessions_by_group_subject = defaultdict(list)
    teacher_load = defaultdict(int)
    group_lunch = {
        group.id: set(group.lunch_break_periods)
        for group in problem.student_groups
    }

    teachers = {teacher.id: teacher for teacher in problem.teachers}
    groups = {group.id: group for group in problem.student_groups}

    for session in timetable.sessions:
        assignment = session.assignment
        sessions_by_group_subject[
            (session.group_id, session.subject_id)
        ].append(session)

        teacher_load[assignment.teacher_id] += session.duration_slots

        if session.group_id not in groups:
            violations.append(
                f"Unknown student group: {session.group_id}"
            )
        elif any(
            period in group_lunch[session.group_id]
            for period in range(
                assignment.start_period,
                assignment.start_period + session.duration_slots,
            )
        ):
            violations.append(
                f"Lunch break violation: {session.session_id}"
            )

        if assignment.teacher_id not in teachers:
            violations.append(
                f"Unknown teacher: {assignment.teacher_id}"
            )
    # H7: Reject sessions that are not part of a declared requirement.
    required_group_subjects = {
        (group.id, requirement.subject_id)
        for group in problem.student_groups
        for requirement in group.subject_requirements
    }

    for session in timetable.sessions:
        key = (session.group_id, session.subject_id)

        if (
            session.group_id in groups
            and key not in required_group_subjects
        ):
            violations.append(
                "Unrequested subject session: "
                f"group {session.group_id} has no requirement "
                f"for subject {session.subject_id}"
            )

    for group in problem.student_groups:
        for requirement in group.subject_requirements:
            scheduled = sessions_by_group_subject[
                (group.id, requirement.subject_id)
            ]

            if len(scheduled) != requirement.weekly_sessions:
                violations.append(
                    f"Weekly session count violation: "
                    f"{group.id}, {requirement.subject_id}"
                )

            total_slots = sum(
                session.duration_slots for session in scheduled
            )
            required_slots = (
                requirement.weekly_sessions * requirement.duration_slots
            )

            if total_slots != required_slots:
                violations.append(
                    f"Weekly hours violation: "
                    f"{group.id}, {requirement.subject_id}"
                )
            for session in scheduled:
                if session.duration_slots != requirement.duration_slots:
                    violations.append(
                        f"Session duration violation: {session.session_id}, "
                        f"expected {requirement.duration_slots}, "
                        f"got {session.duration_slots}"
                    )

    for teacher in problem.teachers:
        if teacher_load[teacher.id] > teacher.maximum_weekly_load:
            violations.append(
                f"Teacher workload violation: {teacher.id}"
            )

    return violations