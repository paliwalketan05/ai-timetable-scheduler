"""Session state management and persistence helpers."""

import streamlit as st
from typing import Any
from src.models.entities import SchedulingProblem
from src.models.schedule import Timetable


def init_session_state():
    """Initialize default keys in st.session_state."""
    defaults: dict[str, Any] = {
        "problem": None,
        "raw_dataframe": None,
        "preprocessing_report": None,
        "validation_errors": None,
        "dataset_name": None,
        "generated_timetable": None,
        "generation_result": None,
        "experiments_history": [],
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def set_loaded_dataset(
    problem: SchedulingProblem,
    df: Any,
    report: dict | None,
    errors: list[str],
    dataset_name: str,
):
    """Store loaded dataset and invalidate old timetable results."""
    st.session_state["problem"] = problem
    st.session_state["raw_dataframe"] = df
    st.session_state["preprocessing_report"] = report
    st.session_state["validation_errors"] = errors
    st.session_state["dataset_name"] = dataset_name
    # Invalidate existing timetable results because dataset changed
    clear_timetable_result()


def clear_loaded_dataset():
    """Clear all dataset and timetable information."""
    st.session_state["problem"] = None
    st.session_state["raw_dataframe"] = None
    st.session_state["preprocessing_report"] = None
    st.session_state["validation_errors"] = None
    st.session_state["dataset_name"] = None
    clear_timetable_result()


def set_timetable_result(timetable: Timetable | None, result_dict: dict):
    """Save newly generated timetable and search metrics."""
    st.session_state["generated_timetable"] = timetable
    st.session_state["generation_result"] = result_dict
    if result_dict:
        st.session_state["experiments_history"].append(result_dict)


def clear_timetable_result():
    """Clear generated timetable and results."""
    st.session_state["generated_timetable"] = None
    st.session_state["generation_result"] = None


def has_dataset() -> bool:
    """Return True if a SchedulingProblem is currently loaded."""
    return st.session_state.get("problem") is not None


def has_timetable() -> bool:
    """Return True if a Timetable has been generated and stored."""
    return st.session_state.get("generated_timetable") is not None
