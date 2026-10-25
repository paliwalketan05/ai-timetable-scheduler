"""Automated tests for Streamlit frontend integration, CSV ingestion, and export logic."""

import io
from pathlib import Path
import pytest
import pandas as pd

from src.models.entities import (
    Subject,
    Teacher,
    StudentGroup,
    SubjectRequirement,
    Room,
    TimeStructure,
    SchedulingProblem,
)
from src.models.schedule import Assignment, ScheduledSession, Timetable
from src.data.loaders import load_timetable_csv
from src.data.validation import validate_timetable_input
from src.csp.sessions import expand_sessions
from src.csp.domains import generate_domains
from src.ui.styles import render_badge
from src.ui.state import init_session_state, set_loaded_dataset, clear_loaded_dataset
from src.ui.views.generate import check_algorithm_implementation
from src.ui.views.validation import check_validator_module
from src.ui.views.export import generate_export_dataframe


def test_ui_modules_import_successfully():
    """Ensure all UI views, styles, and state modules import without syntax or path errors."""
    import src.ui.styles
    import src.ui.state
    import src.ui.views.dashboard
    import src.ui.views.upload
    import src.ui.views.manage_data
    import src.ui.views.generate
    import src.ui.views.timetables
    import src.ui.views.validation
    import src.ui.views.experiments
    import src.ui.views.export
    import src.ui.views.about

    assert hasattr(src.ui.styles, "render_badge")
    assert hasattr(src.ui.state, "init_session_state")


def test_load_sample_csv_fixture():
    """Verify that test_input.csv loads and passes input validation."""
    fixture_path = Path("tests/fixtures/test_input.csv")
    assert fixture_path.exists(), "test_input.csv must exist in tests/fixtures"

    problem, prep_report = load_timetable_csv(fixture_path, return_report=True)

    assert isinstance(problem, SchedulingProblem)
    assert len(problem.subjects) == 1
    assert len(problem.teachers) == 1
    assert len(problem.student_groups) == 1
    assert len(problem.rooms) == 1
    assert problem.time_structure.periods_per_day == 6

    # Validate problem
    val_errors = validate_timetable_input(problem)
    assert val_errors == [], f"Sample fixture had unexpected validation errors: {val_errors}"


def test_csp_expansion_and_domains_on_fixture():
    """Verify session expansion and domain generation on the sample fixture."""
    fixture_path = Path("tests/fixtures/test_input.csv")
    problem = load_timetable_csv(fixture_path)

    sessions = expand_sessions(problem)
    assert len(sessions) == 4  # MAT101 requires 4 sessions
    assert all(s.duration_slots == 1 for s in sessions)

    domains = generate_domains(problem, sessions)
    for session in sessions:
        domain = domains[session.id]
        assert len(domain) > 0, f"Domain for session {session.id} must not be empty"
        # Verify teacher T01 and room R01 assigned
        assert all(a.teacher_id == "T01" for a in domain)
        assert all(a.room_id == "R01" for a in domain)


def test_invalid_csv_handling():
    """Verify that malformed CSV data is safely rejected with informative errors."""
    malformed_csv = io.StringIO(
        "record_type,id,name\n"
        "unknown_type,X01,Mystery\n"
    )
    with pytest.raises(ValueError) as excinfo:
        load_timetable_csv(malformed_csv)

    assert "Unknown record type" in str(excinfo.value)


def test_check_algorithm_implementation_returns_bool():
    """Verify solver availability inspector returns a boolean for real solver modules."""
    res = check_algorithm_implementation("src.solvers.backtracking")
    assert isinstance(res, bool)
    assert res is True


def test_check_validator_module_returns_callable_or_none():
    """Verify validator inspector safely checks for callable functions."""
    func = check_validator_module()
    assert func is None or callable(func)


def test_generate_export_dataframe():
    """Verify that export dataframe builds correct columns from a Timetable."""
    problem = SchedulingProblem(
        subjects=[Subject(id="MAT101", name="Mathematics")],
        teachers=[Teacher(id="T01", name="Prof. Aman")],
        student_groups=[StudentGroup(id="C01", name="Batch A", strength=30)],
        rooms=[Room(id="R01", name="Room 101", capacity=50)],
        time_structure=TimeStructure(working_days=["Monday"], periods_per_day=4),
    )

    asgn = Assignment(
        session_id="C01_MAT101_S1",
        teacher_id="T01",
        day="Monday",
        start_period=1,
        room_id="R01",
    )
    scheduled_s = ScheduledSession(
        session_id="C01_MAT101_S1",
        group_id="C01",
        subject_id="MAT101",
        duration_slots=2,
        assignment=asgn,
    )
    timetable = Timetable(sessions=[scheduled_s])

    df = generate_export_dataframe(problem, timetable)

    assert len(df) == 1
    assert list(df.columns) == [
        "Session ID",
        "Class ID",
        "Class Name",
        "Subject ID",
        "Subject Name",
        "Teacher ID",
        "Teacher Name",
        "Room ID",
        "Room Name",
        "Day",
        "Start Period",
        "Duration (Slots)",
        "End Period",
    ]
    row = df.iloc[0]
    assert row["Class Name"] == "Batch A"
    assert row["Subject Name"] == "Mathematics"
    assert row["Teacher Name"] == "Prof. Aman"
    assert row["Start Period"] == "P1"
    assert row["Duration (Slots)"] == 2
    assert row["End Period"] == "P2"


def test_render_badge_html():
    """Verify badge rendering helper produces valid CSS class spans."""
    badge = render_badge("Passed", "success")
    assert "badge badge-success" in badge
    assert "Passed" in badge


def test_state_dataset_change_invalidates_timetable():
    """Verify that uploading or setting a new dataset invalidates previously generated timetables."""
    import streamlit as st
    init_session_state()

    dummy_problem = SchedulingProblem([], [], [], [], TimeStructure([], 0))
    dummy_tt = Timetable([])

    st.session_state["generated_timetable"] = dummy_tt
    assert st.session_state["generated_timetable"] is not None

    # Load new dataset
    set_loaded_dataset(dummy_problem, None, None, [], "new_data.csv")
    assert st.session_state["generated_timetable"] is None
    assert st.session_state["dataset_name"] == "new_data.csv"

