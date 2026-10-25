
import pandas as pd

from src.models.entities import (
    Subject,
    SubjectRequirement,
    Teacher,
    StudentGroup,
    Room,
    TimeStructure,
    SchedulingProblem,
)


def parse_list(value):
    """Convert a semicolon-separated CSV cell into a list."""
    if pd.isna(value) or not str(value).strip():
        return []

    return [
        item.strip()
        for item in str(value).split(";")
        if item.strip()
    ]


def parse_periods(value):
    """Convert P1;P2 into [1, 2]."""
    periods = []

    for item in parse_list(value):
        if not item.startswith("P") or not item[1:].isdigit():
            raise ValueError(f"Invalid period format: {item}")

        periods.append(int(item[1:]))

    return periods


def parse_subject_requirements(value):
    requirements = []

    for item in parse_list(value):
        parts = [part.strip() for part in item.split(":")]

        if len(parts) not in (2, 3):
            raise ValueError(
                f"Invalid subject requirement {item!r}."
            )

        subject_id = parts[0].upper()
        weekly_sessions = int(parts[1])
        duration_slots = int(parts[2]) if len(parts) == 3 else 1

        if weekly_sessions < 1 or duration_slots < 1:
            raise ValueError(
                "Weekly sessions and duration slots must be positive."
            )

        requirements.append(
            SubjectRequirement(
                subject_id=subject_id,
                weekly_sessions=weekly_sessions,
                duration_slots=duration_slots,
            )
        )

    return requirements


def preprocess_timetable_dataframe(df):
    """Remove exact duplicate rows and report the change."""
    df = df.copy()

    report = {
        "duplicate_rows_removed": 0,
    }

    # Identify duplicate rows, keeping the first occurrence.
    duplicate_mask = df.duplicated(keep="first")

    # Count duplicates before removing them.
    report["duplicate_rows_removed"] = int(duplicate_mask.sum())

    # Remove exact duplicates.
    df = df.drop_duplicates(keep="first")

    return df, report


def preprocess_timetable_dataframe(df):
    """Remove exact duplicate rows and normalize text values."""
    df = df.copy()

    report = {
        "duplicate_rows_removed": 0,
        "text_cells_trimmed": 0,
        "category_values_normalized": 0,
    }

    # 1. Remove exact duplicate rows
    duplicate_mask = df.duplicated(keep="first")
    report["duplicate_rows_removed"] = int(duplicate_mask.sum())
    df = df.drop_duplicates(keep="first")

    # 2. Remove leading and trailing whitespace from text
    for column in df.columns:
        if column not in df.columns:
            continue

        for index in df.index:
            value = df.at[index, column]

            if isinstance(value, str):
                cleaned_value = value.strip()

                if cleaned_value != value:
                    report["text_cells_trimmed"] += 1

                df.at[index, column] = cleaned_value

    # 3. Standardize known categorical fields
    category_columns = {
        "record_type",
        "subject_type",
        "room_type",
    }

    for column in category_columns.intersection(df.columns):
        for index in df.index:
            value = df.at[index, column]

            if isinstance(value, str):
                normalized_value = value.lower()

                if normalized_value != value:
                    report["category_values_normalized"] += 1

                df.at[index, column] = normalized_value

    return df, report


def normalize_list_field(value, field_name):
    """Normalize spacing in semicolon-separated CSV fields."""
    if not isinstance(value, str) or not value.strip():
        return value

    items = value.split(";")
    normalized_items = []

    for item in items:
        item = item.strip()

        if not item:
            continue

        # Subject requirements look like MAT101:3:2
        if field_name == "subject_ids":
            parts = [part.strip() for part in item.split(":")]
            item = ":".join(parts)

        normalized_items.append(item)

    return ";".join(normalized_items)


def normalize_list_like_fields(df, report):
    """Normalize list-like CSV fields."""
    list_columns = {
        "subjects_can_teach",
        "unavailable_slots",
        "working_days",
        "break_periods",
        "lunch_break_slot",
        "subject_ids",
    }

    report["list_fields_normalized"] = 0

    for column in list_columns.intersection(df.columns):
        for index in df.index:
            value = df.at[index, column]
            normalized_value = normalize_list_field(value, column)

            if normalized_value != value:
                report["list_fields_normalized"] += 1

            df.at[index, column] = normalized_value

    return df


def preprocess_timetable_dataframe(df):
    """Remove exact duplicates and normalize text and empty values."""
    df = df.copy()

    
    rows_before = len(df)

    report = {
        "rows_before": rows_before,
        "rows_after": 0,
        "duplicate_rows_removed": 0,
        "text_cells_trimmed": 0,
        "category_values_normalized": 0,
        "empty_cells_normalized": 0,
        "list_fields_normalized": 0,
    }


    # 1. Remove exact duplicate rows
    duplicate_mask = df.duplicated(keep="first")
    report["duplicate_rows_removed"] = int(duplicate_mask.sum())
    df = df.drop_duplicates(keep="first")

    # 2. Normalize text and empty values
    for column in df.columns:
        for index in df.index:
            value = df.at[index, column]

            # Convert missing values such as None or NaN to ""
            if pd.isna(value):
                df.at[index, column] = ""
                report["empty_cells_normalized"] += 1
                continue

            if isinstance(value, str):
                cleaned_value = value.strip()

                if cleaned_value != value:
                    report["text_cells_trimmed"] += 1

                # Convert whitespace-only strings to ""
                if cleaned_value == "" and value != "":
                    report["empty_cells_normalized"] += 1

                df.at[index, column] = cleaned_value

    # 3. Normalize known categorical fields
    category_columns = {
        "record_type",
        "subject_type",
        "room_type",
    }

    for column in category_columns.intersection(df.columns):
        for index in df.index:
            value = df.at[index, column]

            if isinstance(value, str):
                normalized_value = value.lower()

                if normalized_value != value:
                    report["category_values_normalized"] += 1

                df.at[index, column] = normalized_value

    # 4. Normalize list-like CSV fields
    df = normalize_list_like_fields(df, report)

    
    report["rows_after"] = len(df)

    return df, report

def load_timetable_csv(file,return_report=False):
    """Convert a single CSV into a SchedulingProblem."""

    df = pd.read_csv(file, dtype=str)

    df, preprocessing_report = preprocess_timetable_dataframe(df)

    required_columns = {
        "record_type",
        "id",
        "name",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    subjects = []
    teachers = []
    groups = []
    rooms = []
    time_structure = None

    for row_number, row in enumerate(
        df.to_dict(orient="records"), start=2
    ):
        kind = row["record_type"]
        record_id = row["id"]
        name = row["name"]

        try:
            if kind == "subject":
                subjects.append(
                    Subject(
                        id=record_id,
                        name=name,
                        subject_type=(
                            (row.get("subject_type") or "theory").strip().lower()
                        ),
                    )
                )

            elif kind == "teacher":
                teachers.append(
                    Teacher(
                        id=record_id,
                        name=name,
                        subjects_can_teach=parse_list(
                            row.get("subjects_can_teach", "")
                        ),
                        unavailable_slots=parse_list(
                            row.get("unavailable_slots", "")
                        ),
                        maximum_weekly_load=int(
                            row.get("maximum_weekly_load") or 20
                        ),
                    )
                )

            elif kind=="class":
                requirements=parse_subject_requirements(
                    row.get("subject_ids","")
                )

                groups.append(
                    StudentGroup(
                        id=record_id,
                        name=name,
                        strength=int(row.get("strength") or 0),
                        subject_requirements=requirements,
                        lunch_break_periods=parse_periods(
                            row.get("lunch_break_slot", "")
                        ),
                    )
                )

            elif kind == "room":
                rooms.append(
                    Room(
                        id=record_id,
                        name=name,
                        capacity=int(row.get("capacity") or 0),
                        room_type=(
                            (row.get("room_type") or "classroom").strip().lower()
                        ),
                    )
                )

            elif kind == "settings":
                if time_structure is not None:
                    raise ValueError(
                        "Only one settings record is allowed"
                    )

                time_structure = TimeStructure(
                    working_days=parse_list(
                        row.get("working_days", "")
                    ),
                    periods_per_day=int(
                        row.get("periods_per_day") or 0
                    ),
                    break_periods=parse_periods(
                        row.get("break_periods", "")
                    ),
                    period_duration_minutes=int(
                        row.get("period_duration_minutes") or 50
                    ),
                )

            else:
                raise ValueError(
                    f"Unknown record type: {kind!r}"
                )

        except (ValueError, TypeError) as exc:
            raise ValueError(
                f"CSV row {row_number}: {exc}"
            ) from exc

    if time_structure is None:
        raise ValueError("CSV must contain a settings record.")

    problem = SchedulingProblem(
    subjects=subjects,
    teachers=teachers,
    student_groups=groups,
    rooms=rooms,
    time_structure=time_structure,
    )

    if return_report:
       return problem, preprocessing_report
    
    return problem 