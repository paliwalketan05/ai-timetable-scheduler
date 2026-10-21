
from experiments.datasets import make_small_problem
from src.csp.sessions import expand_sessions
from src.data.validation import validate_timetable_input


def test_small_problem_passes_input_validation():
    problem = make_small_problem()

    assert validate_timetable_input(problem) == []


def test_small_problem_has_expected_entities():
    problem = make_small_problem()

    assert len(problem.subjects) == 3
    assert len(problem.teachers) == 3
    assert len(problem.student_groups) == 2
    assert len(problem.rooms) == 3


def test_small_problem_expands_to_expected_sessions():
    problem = make_small_problem()

    sessions = expand_sessions(problem)

    # Group C01: 3 + 2 + 1 sessions.
    # Group C02: 2 + 3 + 1 sessions.
    assert len(sessions) == 12


def test_small_problem_session_ids_are_unique_strings():
    sessions = expand_sessions(make_small_problem())
    session_ids = [session.id for session in sessions]

    assert all(isinstance(session_id, str) for session_id in session_ids)
    assert len(session_ids) == len(set(session_ids))


def test_small_problem_is_reproducible():
    first = make_small_problem()
    second = make_small_problem()

    assert first == second
