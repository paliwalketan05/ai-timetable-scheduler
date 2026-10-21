
from src.csp.sessions import expand_sessions
from src.models.entities import (
    SchedulingProblem,
    Subject,
    SubjectRequirement,
    StudentGroup,
    Teacher,
    Room,
    TimeStructure,
)


def make_problem():
    return SchedulingProblem(
        subjects=[
            Subject(id="MAT101", name="Mathematics"),
            Subject(id="CHEM101", name="Chemistry"),
        ],
        teachers=[],
        student_groups=[
            StudentGroup(
                id="CS-A",
                name="Computer Science A",
                strength=30,
                subject_requirements=[
                    SubjectRequirement(
                        subject_id="MAT101",
                        weekly_sessions=4,
                        duration_slots=1,
                    ),
                    SubjectRequirement(
                        subject_id="CHEM101",
                        weekly_sessions=2,
                        duration_slots=2,
                    ),
                ],
            )
        ],
        rooms=[],
        time_structure=TimeStructure(
            working_days=["Monday", "Tuesday", "Wednesday"],
            periods_per_day=6,
        ),
    )


def test_expand_sessions_creates_all_required_sessions():
    sessions = expand_sessions(make_problem())

    assert len(sessions) == 6


def test_expand_sessions_preserves_durations():
    sessions = expand_sessions(make_problem())

    chemistry_sessions = [
        session for session in sessions
        if session.subject_id == "CHEM101"
    ]

    assert len(chemistry_sessions) == 2
    assert all(
        session.duration_slots == 2
        for session in chemistry_sessions
    )


def test_expand_sessions_generates_unique_ids():
    sessions = expand_sessions(make_problem())

    session_ids = [session.id for session in sessions]

    assert len(session_ids) == len(set(session_ids))


def test_expand_sessions_preserves_group_and_subject_ids():
    sessions = expand_sessions(make_problem())

    assert all(session.group_id == "CS-A" for session in sessions)
    assert {session.subject_id for session in sessions} == {
        "MAT101",
        "CHEM101",
    }

def test_session_ids_are_unique_strings():
    problem = make_problem()
    sessions = expand_sessions(problem)

    session_ids = [session.id for session in sessions]

    assert all(isinstance(session_id, str) for session_id in session_ids)
    assert len(session_ids) == len(set(session_ids))