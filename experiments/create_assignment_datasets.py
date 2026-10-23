
"""Create the two datasets required by the timetable assignment."""

import csv
from pathlib import Path

OUTPUT_DIR = Path("experiments/datasets")

COLUMNS = [
    "record_type",
    "id",
    "name",
    "subject_type",
    "subjects_can_teach",
    "unavailable_slots",
    "maximum_weekly_load",
    "strength",
    "subject_ids",
    "lunch_break_slot",
    "capacity",
    "room_type",
    "working_days",
    "periods_per_day",
    "break_periods",
    "period_duration_minutes",
]

DAYS = "Monday;Tuesday;Wednesday;Thursday;Friday"


def build_dataset(
    *,
    class_count: int,
    teacher_count_per_subject: int,
    classroom_count: int,
    lab_count: int,
    periods_per_day: int,
) -> list[dict[str, str]]:
    rows = []

    def add(record_type: str, record_id: str, name: str, **fields):
        row = {column: "" for column in COLUMNS}
        row.update(
            record_type=record_type,
            id=record_id,
            name=name,
        )
        row.update({key: str(value) for key, value in fields.items()})
        rows.append(row)

    # Three subjects, including a two-period laboratory session.
    add("subject", "MAT101", "Mathematics", subject_type="theory")
    add("subject", "PHY101", "Physics", subject_type="theory")
    add("subject", "CHEM101", "Chemistry Laboratory", subject_type="lab")

    # Each subject has multiple qualified teachers.
    subject_specs = [
        ("MAT101", "Mathematics"),
        ("PHY101", "Physics"),
        ("CHEM101", "Chemistry"),
    ]

    teacher_number = 1

    for subject_id, subject_name in subject_specs:
        for _ in range(teacher_count_per_subject):
            teacher_id = f"T{teacher_number:02d}"
            add(
                "teacher",
                teacher_id,
                f"{subject_name} Teacher {teacher_number}",
                subjects_can_teach=subject_id,
                maximum_weekly_load=20,
            )
            teacher_number += 1

    # Classes have modest weekly requirements.
    # Chemistry laboratory sessions occupy two consecutive periods.
    for number in range(1, class_count + 1):
        class_id = f"C{number:02d}"
        strength = 28 + (number % 8)

        add(
            "class",
            class_id,
            f"Class {number:02d}",
            strength=strength,
            subject_ids="MAT101:2;PHY101:2;CHEM101:1:2",
            lunch_break_slot="P4",
        )

    # Classrooms have sufficient capacity for every class.
    for number in range(1, classroom_count + 1):
        add(
            "room",
            f"R{number:02d}",
            f"Classroom {number:02d}",
            capacity=50,
            room_type="classroom",
        )

    for number in range(1, lab_count + 1):
        add(
            "room",
            f"LAB{number:02d}",
            f"Laboratory {number:02d}",
            capacity=50,
            room_type="lab",
        )

    # One settings record defines the timetable structure.
    add(
        "settings",
        "CFG01",
        "Default Settings",
        working_days=DAYS,
        periods_per_day=periods_per_day,
        break_periods="P3" if periods_per_day == 6 else "P4",
        period_duration_minutes=50,
    )

    return rows


def write_dataset(filename: str, rows: list[dict[str, str]]) -> None:
    path = OUTPUT_DIR / filename
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Created {path} ({len(rows)} records)")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    small = build_dataset(
        class_count=3,
        teacher_count_per_subject=2,
        classroom_count=3,
        lab_count=1,
        periods_per_day=6,
    )
    write_dataset("assignment_small.csv", small)

    large = build_dataset(
        class_count=8,
        teacher_count_per_subject=5,
        classroom_count=6,
        lab_count=2,
        periods_per_day=7,
    )
    write_dataset("assignment_large.csv", large)


if __name__ == "__main__":
    main()
