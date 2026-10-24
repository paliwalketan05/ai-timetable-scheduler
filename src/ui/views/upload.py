"""Dataset upload and validation view using src.data.loaders and src.data.validation."""

import io
from pathlib import Path
import streamlit as st
import pandas as pd

from src.data.loaders import load_timetable_csv
from src.data.validation import validate_timetable_input
from src.ui.state import set_loaded_dataset, clear_loaded_dataset
from src.ui.styles import render_badge


SAMPLE_CSV_PATH = Path("tests/fixtures/test_input.csv")

CSV_TEMPLATE = """record_type,id,name,subject_type,subjects_can_teach,unavailable_slots,maximum_weekly_load,strength,subject_ids,lunch_break_slot,capacity,room_type,working_days,periods_per_day,break_periods,period_duration_minutes
subject,MAT101,Mathematics,theory,,,,,,,,,,,
subject,CS102,Data Structures,theory,,,,,,,,,,,
subject,CS102L,Data Structures Lab,lab,,,,,,,,,,,
teacher,T01,Prof. Alan,theory,MAT101;CS102,,20,,,,,,,,
teacher,T02,Dr. Grace,lab,CS102L,Monday_P1,16,,,,,,,,
class,C01,AI Batch A,,,,,40,MAT101:3;CS102:3;CS102L:1:2,P4,,,,,,
room,R01,Lecture Hall 101,,,,,,,,60,classroom,,,,
room,L01,Computing Lab 1,,,,,,,,30,lab,,,,
settings,S01,Default Settings,,,,,,,,,,Monday;Tuesday;Wednesday;Thursday;Friday,6,P4,50
"""


def render_upload_page():
    st.markdown(
        """
        <div class="page-header">
            <h1 class="page-title">Dataset Upload & Ingestion</h1>
            <p class="page-subtitle">Load academic data via CSV, verify record schemas, and inspect preprocessing metrics.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 1. Action buttons: Upload or Load Sample Fixture
    col_u1, col_u2 = st.columns([3, 2])

    uploaded_file = None
    use_sample = False

    with col_u1:
        uploaded_file = st.file_uploader(
            "Upload Institution CSV File",
            type=["csv"],
            help="Select a CSV formatted according to the system's schema.",
        )

    with col_u2:
        st.markdown("**Quick Test with Sample Data:**")
        if SAMPLE_CSV_PATH.exists():
            if st.button("📥 Load Built-in Test Dataset (`test_input.csv`)", use_container_width=True):
                use_sample = True
        else:
            st.caption("Sample fixture file not found in tests/fixtures.")

        st.download_button(
            label="📄 Download CSV Schema Template",
            data=CSV_TEMPLATE,
            file_name="timetable_template.csv",
            mime="text/csv",
            use_container_width=True,
        )

    # Determine data source to parse
    data_source = None
    source_name = ""

    if uploaded_file is not None:
        data_source = uploaded_file
        source_name = uploaded_file.name
    elif use_sample and SAMPLE_CSV_PATH.exists():
        with open(SAMPLE_CSV_PATH, "rb") as f:
            data_source = io.BytesIO(f.read())
        source_name = "test_input.csv (Built-in Test Fixture)"

    # Process ingestion if data source is provided
    if data_source is not None:
        try:
            # We call the existing load_timetable_csv from src.data.loaders with return_report=True
            problem, prep_report = load_timetable_csv(data_source, return_report=True)
            
            # Reset buffer to get a raw pandas dataframe preview
            if hasattr(data_source, "seek"):
                data_source.seek(0)
            raw_df = pd.read_csv(data_source, dtype=str)

            # Validate using existing validate_timetable_input
            val_errors = validate_timetable_input(problem)

            # Store in session state
            set_loaded_dataset(problem, raw_df, prep_report, val_errors, source_name)
            st.success(f"Successfully loaded and preprocessed dataset: **{source_name}**")

        except Exception as exc:
            st.error(f"❌ Failed to load CSV: {exc}")
            return

    # Check if a problem is currently stored in session state
    problem = st.session_state.get("problem")
    raw_df = st.session_state.get("raw_dataframe")
    prep_report = st.session_state.get("preprocessing_report")
    val_errors = st.session_state.get("validation_errors", [])

    if problem is None or raw_df is None:
        st.markdown("---")
        st.markdown("### Expected CSV Schema")
        st.info(
            "The scheduling system requires a single unified CSV file with specific `record_type` values:\n\n"
            "- **`subject`**: id, name, subject_type (`theory` or `lab`)\n"
            "- **`teacher`**: id, name, subjects_can_teach (semicolon-separated), unavailable_slots, maximum_weekly_load\n"
            "- **`class`**: id, name, strength, subject_ids (`CODE:sessions:duration`), lunch_break_slot (`P4`)\n"
            "- **`room`**: id, name, capacity, room_type (`classroom` or `lab`)\n"
            "- **`settings`**: working_days, periods_per_day, break_periods (`P4`), period_duration_minutes\n",
            icon="📋",
        )
        return

    # 2. Display Ingestion Reports
    st.markdown("---")
    st.subheader(f"Dataset Details: {st.session_state.get('dataset_name')}")

    # Top stats
    r1, r2, r3, r4 = st.columns(4)
    with r1:
        st.metric("Total Rows", len(raw_df))
    with r2:
        st.metric("Total Columns", len(raw_df.columns))
    with r3:
        record_counts = raw_df["record_type"].value_counts().to_dict() if "record_type" in raw_df.columns else {}
        distinct_types = len(record_counts)
        st.metric("Record Types", distinct_types)
    with r4:
        missing_count = int(raw_df.isna().sum().sum())
        st.metric("Empty Fields", missing_count)

    # 3. Preprocessing Report Display
    if prep_report:
        st.markdown("#### Preprocessing Summary")
        p1, p2, p3, p4 = st.columns(4)
        with p1:
            st.metric("Duplicates Removed", prep_report.get("duplicate_rows_removed", 0))
        with p2:
            st.metric("Cells Trimmed", prep_report.get("text_cells_trimmed", 0))
        with p3:
            st.metric("Categories Standardized", prep_report.get("category_values_normalized", 0))
        with p4:
            st.metric("List Fields Cleaned", prep_report.get("list_fields_normalized", 0))

    # 4. Input Validation Results
    st.markdown("#### Input Validation Status")
    if not val_errors:
        st.markdown(
            f"""
            <div style="background-color:#ecfdf5; border:1px solid #a7f3d0; border-radius:8px; padding:12px 16px; color:#065f46; font-size:0.92rem;">
                ✅ <strong>Validation Passed:</strong> The loaded dataset satisfies all foreign keys, entity bounds, capacity thresholds, and time structure consistency checks.
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div style="background-color:#fef2f2; border:1px solid #fecaca; border-radius:8px; padding:12px 16px; color:#991b1b; font-size:0.92rem;">
                ⚠️ <strong>Validation Issues Detected ({len(val_errors)} error{'s' if len(val_errors) > 1 else ''}):</strong>
                Input violations must be addressed before running the scheduling algorithm.
            </div>
            """,
            unsafe_allow_html=True,
        )
        for err in val_errors:
            st.error(f"&bull; {err}")

    # 5. Raw Data Preview
    st.markdown("#### Raw CSV Data Preview")
    st.dataframe(raw_df, use_container_width=True, height=260)

    # 6. Unload button
    if st.button("🗑️ Unload Current Dataset", type="secondary"):
        clear_loaded_dataset()
        st.rerun()
