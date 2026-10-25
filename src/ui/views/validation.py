"""Constraint Validation view displaying status and violation reports for H1-H9 and S1-S5."""

import importlib
import streamlit as st
import pandas as pd
from typing import Any

from src.models.entities import SchedulingProblem
from src.models.schedule import Timetable
from src.ui.styles import render_badge


HARD_CONSTRAINTS = [
    {
        "id": "H1",
        "name": "Teacher Double-Booking",
        "description": "A teacher cannot teach two different sessions at the same time slot.",
        "category": "Resource Concurrency",
    },
    {
        "id": "H2",
        "name": "Class/Group Double-Booking",
        "description": "A student group/class cannot attend two sessions simultaneously.",
        "category": "Resource Concurrency",
    },
    {
        "id": "H3",
        "name": "Room Double-Booking",
        "description": "A room cannot host two separate sessions at the same time slot.",
        "category": "Resource Concurrency",
    },
    {
        "id": "H4",
        "name": "Room Capacity Sufficiency",
        "description": "The assigned room capacity must be greater than or equal to student class strength.",
        "category": "Physical Fit",
    },
    {
        "id": "H5",
        "name": "Room Type Compatibility",
        "description": "Laboratory sessions must use lab rooms; theory sessions must use standard classrooms.",
        "category": "Facility Type",
    },
    {
        "id": "H6",
        "name": "Teacher Availability",
        "description": "Teachers must not be assigned to time slots marked in their unavailable slots list.",
        "category": "Instructor Schedule",
    },
    {
        "id": "H7",
        "name": "Required Weekly Sessions",
        "description": "Every subject for each class must receive exactly its prescribed weekly teaching sessions.",
        "category": "Curriculum",
    },
    {
        "id": "H8",
        "name": "Teacher Maximum Weekly Load",
        "description": "The total periods assigned to a teacher must not exceed their maximum weekly workload limit.",
        "category": "Instructor Workload",
    },
    {
        "id": "H9",
        "name": "Lunch Break Protection",
        "description": "No class may have a teaching session during its designated lunch break period.",
        "category": "Wellbeing",
    },
]

SOFT_CONSTRAINTS = [
    {
        "id": "S1",
        "name": "Minimize Student Schedule Gaps",
        "description": "Minimize idle gaps/free periods between lectures during a student group's day.",
        "weight": "Medium",
    },
    {
        "id": "S2",
        "name": "Spread Subjects Across Days",
        "description": "Distribute sessions of the same subject across different days rather than clustering.",
        "weight": "High",
    },
    {
        "id": "S3",
        "name": "Consecutive Lab Slots",
        "description": "Ensure multi-hour laboratory sessions occur in contiguous periods without interruptions.",
        "weight": "High",
    },
    {
        "id": "S4",
        "name": "Faculty Preferences",
        "description": "Respect teacher scheduling preferences, such as avoiding early first-period classes.",
        "weight": "Low",
    },
    {
        "id": "S5",
        "name": "Limit Consecutive Lectures",
        "description": "Avoid assigning more than two consecutive lecture periods for an instructor without a rest slot.",
        "weight": "Medium",
    },
]


def check_validator_module() -> Any:
    """Check if src.evaluation.validator has callable verification functions."""
    try:
        mod = importlib.import_module("src.evaluation.validator")
        for attr in ["validate_timetable", "check_hard_constraints", "validate_schedule"]:
            if hasattr(mod, attr) and callable(getattr(mod, attr)):
                return getattr(mod, attr)
        return None
    except Exception:
        return None


def render_validation_page():
    st.markdown(
        """
        <div class="page-header">
            <h1 class="page-title">Constraint Validation Engine</h1>
            <p class="page-subtitle">Verification checklist for the 9 mandatory Hard Constraints and 5 optimization Soft Constraints.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    problem: SchedulingProblem | None = st.session_state.get("problem")
    timetable: Timetable | None = st.session_state.get("generated_timetable")

    if problem is None:
        st.warning("⚠️ No dataset loaded. Please upload a dataset first.")
        if st.button("📁 Go to Upload Dataset"):
            st.session_state["nav_selection"] = "Upload Dataset"
            st.rerun()
        return

    validator_func = check_validator_module()
    has_active_timetable = timetable is not None

    st.subheader("Hard Constraints (H1 – H9)")
    st.markdown(
        "Mandatory constraints that must have **zero violations** for a timetable to be deemed legally valid."
    )

    # Check validation results if validator_func and timetable exist
    validation_results = {}
    if has_active_timetable and validator_func is not None:
        try:
            validation_results = validator_func(problem, timetable)
        except Exception as exc:
            st.warning(f"Error running validator: {exc}")

    # Build hard constraint rows
    hard_table_data = []
    for hc in HARD_CONSTRAINTS:
        cid = hc["id"]

        if not has_active_timetable:
            status = "Not Applicable (No Timetable)"
            badge_type = "neutral"
            violations = "—"
            details = "Generate a timetable first to validate assignments."
        elif validator_func is None:
            status = "Not Checked (Validator Pending)"
            badge_type = "warning"
            violations = "N/A"
            details = "Independent validation function not yet implemented in src/evaluation/validator.py."
        else:
            # Check results from validator
            res = validation_results.get(cid)
            if res is None:
                status = "Not Checked"
                badge_type = "neutral"
                violations = "N/A"
                details = "Constraint not returned by current validator."
            elif isinstance(res, dict):
                v_count = res.get("violations", 0)
                violations = str(v_count)
                if v_count == 0:
                    status = "Passed"
                    badge_type = "success"
                    details = "0 violations detected."
                else:
                    status = "Failed"
                    badge_type = "danger"
                    details = res.get("explanation", f"{v_count} violation(s) found.")
            else:
                status = "Passed" if res else "Failed"
                badge_type = "success" if res else "danger"
                violations = "0" if res else "Violated"
                details = ""

        hard_table_data.append(
            {
                "ID": cid,
                "Constraint Name": hc["name"],
                "Category": hc["category"],
                "Status": status,
                "Violations": violations,
                "Description": hc["description"],
                "Details": details,
            }
        )

    st.dataframe(pd.DataFrame(hard_table_data), use_container_width=True)

    st.markdown("---")
    st.subheader("Soft Constraints & Quality Scoring (S1 – S5)")
    st.markdown(
        "Institutional preferences used to evaluate timetable quality and comfort. "
        "A valid timetable may have soft penalties, but optimization algorithms aim to minimize them."
    )

    soft_table_data = []
    for sc in SOFT_CONSTRAINTS:
        cid = sc["id"]
        if not has_active_timetable:
            status = "Not Checked"
            penalty = "—"
        elif validator_func is None:
            status = "Not Checked (Pending Backend)"
            penalty = "N/A"
        else:
            res = validation_results.get(cid)
            status = "Calculated" if res is not None else "Not Checked"
            penalty = str(res) if res is not None else "N/A"

        soft_table_data.append(
            {
                "ID": cid,
                "Preference Name": sc["name"],
                "Weight / Priority": sc["weight"],
                "Status": status,
                "Penalty Score": penalty,
                "Rule Description": sc["description"],
            }
        )

    st.dataframe(pd.DataFrame(soft_table_data), use_container_width=True)

    # Explanation Card
    st.markdown(
        """
        <div class="callout-info">
            <strong>Evaluation Standard (from Architecture Specification):</strong><br>
            Objective Cost Function: <code>Cost = 1000 &times; H + S</code><br>
            Where <code>H</code> is the count of hard constraint violations (must be 0 for validity), and <code>S</code> is the weighted soft constraint penalty score.
        </div>
        """,
        unsafe_allow_html=True,
    )
