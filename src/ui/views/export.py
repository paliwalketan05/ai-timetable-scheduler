"""Export Timetable view for generating and downloading CSV and Excel (.xlsx) files."""

import io
import streamlit as st
import pandas as pd

from src.models.entities import SchedulingProblem
from src.models.schedule import Timetable


def generate_export_dataframe(problem: SchedulingProblem, timetable: Timetable) -> pd.DataFrame:
    """Transform Timetable scheduled sessions into a clean exportable DataFrame."""
    subjects_map = {s.id: s.name for s in problem.subjects}
    teachers_map = {t.id: t.name for t in problem.teachers}
    rooms_map = {r.id: r.name for r in problem.rooms}
    groups_map = {g.id: g.name for g in problem.student_groups}

    rows = []
    for s in timetable.sessions:
        asgn = s.assignment
        start_p = asgn.start_period
        duration = s.duration_slots
        end_p = start_p + duration - 1

        rows.append(
            {
                "Session ID": s.session_id,
                "Class ID": s.group_id,
                "Class Name": groups_map.get(s.group_id, s.group_id),
                "Subject ID": s.subject_id,
                "Subject Name": subjects_map.get(s.subject_id, s.subject_id),
                "Teacher ID": asgn.teacher_id,
                "Teacher Name": teachers_map.get(asgn.teacher_id, asgn.teacher_id),
                "Room ID": asgn.room_id,
                "Room Name": rooms_map.get(asgn.room_id, asgn.room_id),
                "Day": asgn.day,
                "Start Period": f"P{start_p}",
                "Duration (Slots)": duration,
                "End Period": f"P{end_p}",
            }
        )

    df = pd.DataFrame(rows)
    # Sort logically by Day, Start Period, Class
    if not df.empty and "Day" in df.columns and "Start Period" in df.columns:
        df = df.sort_values(by=["Class Name", "Day", "Start Period"])
    return df


def render_export_page():
    st.markdown(
        """
        <div class="page-header">
            <h1 class="page-title">Export Timetable</h1>
            <p class="page-subtitle">Download master schedules in structured CSV or Microsoft Excel (.xlsx) formats.</p>
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

    if timetable is None:
        st.info(
            "🔒 **No timetable is available for export.**\n\n"
            "To export schedules, you must first generate a timetable using the **Generate Timetable** workflow. "
            "Fabricated export files are not permitted.",
            icon="ℹ️",
        )
        if st.button("⚡ Go to Generate Timetable"):
            st.session_state["nav_selection"] = "Generate Timetable"
            st.rerun()
        return

    # Build real export dataframe
    export_df = generate_export_dataframe(problem, timetable)

    st.subheader("Timetable Export Preview")
    st.markdown(f"Total scheduled sessions: **{len(export_df)}**")
    st.dataframe(export_df, use_container_width=True)

    # Export buttons
    c_exp1, c_exp2 = st.columns(2)

    # 1. CSV Export
    csv_data = export_df.to_csv(index=False).encode("utf-8")
    with c_exp1:
        st.download_button(
            label="📥 Download Schedule as CSV",
            data=csv_data,
            file_name="generated_timetable.csv",
            mime="text/csv",
            use_container_width=True,
        )

    # 2. Excel Export
    with c_exp2:
        try:
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                export_df.to_excel(writer, index=False, sheet_name="Master Schedule")
            excel_data = excel_buffer.getvalue()

            st.download_button(
                label="📊 Download Schedule as Excel (.xlsx)",
                data=excel_data,
                file_name="generated_timetable.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        except Exception as exc:
            st.caption(f"Excel generation unavailable: {exc}")
