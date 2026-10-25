
from src.models.entities import SchedulingProblem


def validate_timetable_input(
    problem: SchedulingProblem,
) -> list[str]:
    """Return a list of input-data errors before scheduling begins."""

    errors = []

    # 1. Validate entity IDs.
    collections = {
        "Subject": problem.subjects,
        "Teacher": problem.teachers,
        "Class": problem.student_groups,
        "Room": problem.rooms,
    }

    for entity_name, entities in collections.items():
        seen_ids = set()

        for entity in entities:
            entity_id = entity.id

            if not isinstance(entity_id, str) or not entity_id.strip():
                errors.append(
                    f"{entity_name} has an empty or invalid ID."
                )
                continue

            if entity_id in seen_ids:
                errors.append(
                    f"Duplicate ID {entity_id!r} in "
                    f"{entity_name} records."
                )

            seen_ids.add(entity_id)

    # 2. Validate subjects.
    subject_ids = {
        subject.id
        for subject in problem.subjects
        if isinstance(subject.id, str) and subject.id.strip()
    }

    for subject in problem.subjects:
        if not isinstance(subject.name, str) or not subject.name.strip():
            errors.append(
                f"Subject {subject.id!r} must have a name."
            )

        subject_type = (
            subject.subject_type.strip().lower()
            if isinstance(subject.subject_type, str)
            else ""
        )

        if subject_type not in {"theory", "lab"}:
            errors.append(
                f"Subject {subject.id!r} has invalid type "
                f"{subject.subject_type!r}. Use 'theory' or 'lab'."
            )

    # 3. Validate teachers.
    for teacher in problem.teachers:
        if not isinstance(teacher.name, str) or not teacher.name.strip():
            errors.append(
                f"Teacher {teacher.id!r} must have a name."
            )

        if teacher.maximum_weekly_load <= 0:
            errors.append(
                f"Teacher {teacher.id!r} must have a positive "
                "maximum weekly load."
            )

        for subject_id in teacher.subjects_can_teach:
            if subject_id not in subject_ids:
                errors.append(
                    f"Teacher {teacher.id!r} references unknown "
                    f"subject {subject_id!r}."
                )

    # 4. Validate timetable settings before checking period numbers.
    settings = problem.time_structure

    if not settings.working_days:
        errors.append("At least one working day is required.")

    normalized_days = [
        day.strip().casefold()
        for day in settings.working_days
        if isinstance(day, str) and day.strip()
    ]

    if len(normalized_days) != len(settings.working_days):
        errors.append(
            "Working days must contain non-empty day names."
        )

    if len(normalized_days) != len(set(normalized_days)):
        errors.append("Working days must not contain duplicates.")

    if settings.periods_per_day <= 0:
        errors.append("Periods per day must be positive.")

    if settings.period_duration_minutes <= 0:
        errors.append("Period duration must be positive.")

    periods_per_day = settings.periods_per_day

    if periods_per_day > 0:
        valid_periods = set(range(1, periods_per_day + 1))

        for period in settings.break_periods:
            if period not in valid_periods:
                errors.append(
                    f"Break period {period} is outside the valid "
                    f"range 1-{periods_per_day}."
                )

        if len(settings.break_periods) != len(set(settings.break_periods)):
            errors.append("Break periods must not contain duplicates.")

    # 5. Validate classes and their subject requirements.
    for group in problem.student_groups:
        if not isinstance(group.name, str) or not group.name.strip():
            errors.append(
                f"Class {group.id!r} must have a name."
            )

        if group.strength <= 0:
            errors.append(
                f"Class {group.id!r} must have positive strength."
            )

        if periods_per_day > 0:
            valid_periods = set(range(1, periods_per_day + 1))

            for period in group.lunch_break_periods:
                if period not in valid_periods:
                    errors.append(
                        f"Class {group.id!r} has lunch period "
                        f"{period} outside the valid range "
                        f"1-{periods_per_day}."
                    )

            if (
                len(group.lunch_break_periods)
                != len(set(group.lunch_break_periods))
            ):
                errors.append(
                    f"Class {group.id!r} has duplicate lunch periods."
                )

        total_required_slots = 0

        for requirement in group.subject_requirements:
            if requirement.subject_id not in subject_ids:
                errors.append(
                    f"Class {group.id!r} references unknown subject "
                    f"{requirement.subject_id!r}."
                )
                continue

            if requirement.weekly_sessions <= 0:
                errors.append(
                    f"Class {group.id!r}, subject "
                    f"{requirement.subject_id!r}: weekly sessions "
                    "must be positive."
                )
                continue

            if requirement.duration_slots <= 0:
                errors.append(
                    f"Class {group.id!r}, subject "
                    f"{requirement.subject_id!r}: duration slots "
                    "must be positive."
                )
                continue

            total_required_slots += (
                requirement.weekly_sessions
                * requirement.duration_slots
            )

        # Check the class's total weekly teaching demand.
        if settings.working_days and periods_per_day > 0:
            daily_available = periods_per_day - len(
                set(settings.break_periods)
            )

            daily_available = max(0, daily_available)

            for period in group.lunch_break_periods:
                if period not in set(settings.break_periods):
                    daily_available -= 1

            weekly_available = (
                max(0, daily_available)
                * len(settings.working_days)
            )

            if total_required_slots > weekly_available:
                errors.append(
                    f"Class {group.id!r} requires "
                    f"{total_required_slots} teaching periods per week, "
                    f"but has only {weekly_available} available."
                )

    # 6. Validate rooms.
    for room in problem.rooms:
        if not isinstance(room.name, str) or not room.name.strip():
            errors.append(
                f"Room {room.id!r} must have a name."
            )

        if room.capacity <= 0:
            errors.append(
                f"Room {room.id!r} must have positive capacity."
            )

        room_type = (
            room.room_type.strip().lower()
            if isinstance(room.room_type, str)
            else ""
        )

        if room_type not in {"classroom", "lab"}:
            errors.append(
                f"Room {room.id!r} has invalid type "
                f"{room.room_type!r}. Use 'classroom' or 'lab'."
            )

    return errors
