import pytest

from src.models.entities import (
    Subject,
    Teacher,
    SubjectRequirement,
    StudentGroup,
    Room,
    TimeStructure,
    SchedulingProblem,
)
from src.data.validation import validate_timetable_input


@pytest.fixture
def sample_problem():
    """Create reusable test data for validator tests."""
    return SchedulingProblem(
        subjects=[
            Subject(id="MAT101", name="Mathematics")
        ],
        teachers=[
            Teacher(
                id="T01",
                name="Aman",
                subjects_can_teach=["MAT101"],
                maximum_weekly_load=20,
            )
        ],
        student_groups=[
            StudentGroup(
                id="C01",
                name="AI Batch A",
                strength=40,
                subject_requirements=[
                    SubjectRequirement(
                        subject_id="MAT101",
                        weekly_sessions=4,
                    )
                ],
            )
        ],
        rooms=[
            Room(
                id="R01",
                name="Room 101",
                capacity=60,
            )
        ],
        time_structure=TimeStructure(
            working_days=[
                "Monday", "Tuesday", "Wednesday",
                "Thursday", "Friday",
            ],
            periods_per_day=6,
        ),
    )


def test_valid_problem_passes_validation(sample_problem):
    errors = validate_timetable_input(sample_problem)

    assert errors == []


def test_unknown_subject_is_rejected(sample_problem):
    sample_problem.student_groups[0].subject_requirements[0].subject_id = (
        "MAT999"
    )

    errors = validate_timetable_input(sample_problem)

    assert any("MAT999" in error for error in errors)