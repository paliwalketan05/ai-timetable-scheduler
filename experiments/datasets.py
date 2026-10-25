
"""Reusable deterministic datasets for scheduler experiments."""

from src.models.entities import (
    Room,
    SchedulingProblem,
    StudentGroup,
    Subject,
    SubjectRequirement,
    Teacher,
    TimeStructure,
)


def make_small_problem() -> SchedulingProblem:
    """Build a small, realistic scheduling problem for testing."""
    subjects = [
        Subject("MAT101", "Mathematics", "theory"),
        Subject("PHY101", "Physics", "theory"),
        Subject("CHEM101", "Chemistry", "lab"),
    ]

    teachers = [
        Teacher("T01", "Aman", ["MAT101", "PHY101"], [], 20),
        Teacher("T02", "Riya", ["CHEM101"], ["Monday_P1"], 15),
        Teacher("T03", "Kabir", ["PHY101"], [], 15),
    ]

    student_groups = [
        StudentGroup(
            id="C01",
            name="AI Batch A",
            strength=30,
            subject_requirements=[
                SubjectRequirement("MAT101", 3),
                SubjectRequirement("PHY101", 2),
                SubjectRequirement("CHEM101", 1, duration_slots=2),
            ],
            lunch_break_periods=[4],
        ),
        StudentGroup(
            id="C02",
            name="AI Batch B",
            strength=24,
            subject_requirements=[
                SubjectRequirement("MAT101", 2),
                SubjectRequirement("PHY101", 3),
                SubjectRequirement("CHEM101", 1, duration_slots=2),
            ],
            lunch_break_periods=[4],
        ),
    ]

    rooms = [
        Room("R01", "Room 101", 40, "classroom"),
        Room("R02", "Room 102", 30, "classroom"),
        Room("LAB01", "Chemistry Lab", 32, "lab"),
    ]

    time_structure = TimeStructure(
        working_days=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        periods_per_day=6,
        break_periods=[3],
        period_duration_minutes=50,
    )

    return SchedulingProblem(
        subjects=subjects,
        teachers=teachers,
        student_groups=student_groups,
        rooms=rooms,
        time_structure=time_structure,
    )
