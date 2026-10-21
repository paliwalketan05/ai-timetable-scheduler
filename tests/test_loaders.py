import pytest 
import pandas as pd
from src.data.loaders import preprocess_timetable_dataframe
from src.data.loaders import parse_subject_requirements
from src.data.loaders import load_timetable_csv

def test_parse_requirements_without_duration():
    result=parse_subject_requirements("MATh101:4")

    assert len(result)==1
    assert result[0].subject_id=="MATH101"
    assert result[0].weekly_sessions==4
    assert result[0].duration_slots==1


def test_parse_multiple_requirements():
    result = parse_subject_requirements(
        "MATH101:4:1;CHEM101:1:2"
    )

    assert len(result) == 2
    assert result[0].weekly_sessions == 4
    assert result[1].duration_slots == 2


@pytest.mark.parametrize(
    "value",
    [
        "MATH101",
        "MATH101:abc",
        "MATH101:0",
        "MATH101:2:0",
        "MATH101:2:abc",
        "MATH101:2:1:3",
    ],
)

def test_invalid_subject_requirements_are_rejected(value):
    with pytest.raises(ValueError):
        parse_subject_requirements(value)


def test_preprocessing_removes_exact_duplicate_rows():
    df = pd.DataFrame(
        [
            {"record_type": "subject", "id": "MAT101", "name": "Math"},
            {"record_type": "subject", "id": "MAT101", "name": "Math"},
            {"record_type": "teacher", "id": "T01", "name": "Aman"},
        ]
    )

    cleaned_df, report = preprocess_timetable_dataframe(df)

    assert len(cleaned_df) == 2
    assert report["duplicate_rows_removed"] == 1
    assert len(df) == 3


def test_preprocessing_normalizes_text_values():
    df = pd.DataFrame([
        {
            "record_type": "  SUBJECT  ",
            "id": " MAT101 ",
            "name": "  Mathematics  ",
            "subject_type": " THEORY ",
        }
    ])

    cleaned_df, report = preprocess_timetable_dataframe(df)

    assert cleaned_df.iloc[0]["record_type"] == "subject"
    assert cleaned_df.iloc[0]["id"] == "MAT101"
    assert cleaned_df.iloc[0]["name"] == "Mathematics"
    assert cleaned_df.iloc[0]["subject_type"] == "theory"

    assert report["text_cells_trimmed"] == 4
    assert report["category_values_normalized"] == 2


def test_preprocessing_normalizes_empty_values():
    df = pd.DataFrame([
        {
            "record_type": "subject",
            "id": "MAT101",
            "name": "   ",
            "subject_type": None,
        }
    ])

    cleaned_df, report = preprocess_timetable_dataframe(df)

    assert cleaned_df.iloc[0]["name"] == ""
    assert cleaned_df.iloc[0]["subject_type"] == ""


def test_preprocessing_normalizes_list_fields():
    df = pd.DataFrame([
        {
            "record_type": "teacher",
            "id": "T01",
            "name": "Aman",
            "subjects_can_teach": " MAT101 ; PHY101 ; ",
        },
        {
            "record_type": "class",
            "id": "C01",
            "name": "Class A",
            "subject_ids": " MAT101 : 3 : 2 ; PHY101:2 ",
        },
    ])

    cleaned_df, report = preprocess_timetable_dataframe(df)

    assert cleaned_df.iloc[0]["subjects_can_teach"] == "MAT101;PHY101"
    assert cleaned_df.iloc[1]["subject_ids"] == "MAT101:3:2;PHY101:2"
    assert report["list_fields_normalized"] == 2



def test_preprocessing_preserves_suspicious_data():
    df = pd.DataFrame([
        {
            "record_type": "teacher",
            "id": "T01",
            "name": "Aman",
            "subjects_can_teach": "MAT101;XYZ999",
        },
        {
            "record_type": "teacher",
            "id": "T01",
            "name": "Rahul",
            "subjects_can_teach": "PHY101",
        },
        {
            "record_type": "subject",
            "id": "",
            "name": "Unknown Subject",
        },
    ])

    cleaned_df, report = preprocess_timetable_dataframe(df)

    # Different records with the same ID must be preserved
    assert len(cleaned_df) == 3
    assert cleaned_df["id"].tolist() == ["T01", "T01", ""]

    # Unknown subject references must not be removed
    assert cleaned_df.iloc[0]["subjects_can_teach"] == "MAT101;XYZ999"

    # Missing IDs must not be invented
    assert cleaned_df.iloc[2]["id"] == ""


def test_preprocessing_report_tracks_row_counts():
    df = pd.DataFrame([
        {"record_type": "subject", "id": "MAT101", "name": "Math"},
        {"record_type": "subject", "id": "MAT101", "name": "Math"},
        {"record_type": "teacher", "id": "T01", "name": "Aman"},
    ])

    cleaned_df, report = preprocess_timetable_dataframe(df)

    assert report["rows_before"] == 3
    assert report["rows_after"] == 2
    assert report["duplicate_rows_removed"] == 1
    assert report["rows_before"] - report["rows_after"] == 1

def test_loader_can_return_preprocessing_report():
    from io import StringIO

    csv_data = StringIO(
        "record_type,id,name,subject_type\n"
        "subject,MAT101,Mathematics,theory\n"
        "subject,MAT101,Mathematics,theory\n"
        "settings,CFG01,Settings,"
    )

    problem, report = load_timetable_csv(
        csv_data,
        return_report=True,
    )

    assert len(problem.subjects) == 1
    assert report["rows_before"] == 3
    assert report["rows_after"] == 2
    assert report["duplicate_rows_removed"] == 1