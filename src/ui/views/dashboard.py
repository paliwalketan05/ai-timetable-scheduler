"""Dashboard view displaying dataset KPIs, system status, and recent solver runs."""

import streamlit as st
from src.ui.styles import render_kpi_card, render_badge
from src.csp.sessions import expand_sessions


def render_dashboard_page():
    st.markdown(
        """
        <div class="page-header">
            <h1 class="page-title">Academic Scheduling Dashboard</h1>
            <p class="page-subtitle">Overview of academic entities, time structure, and timetable generation state.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    problem = st.session_state.get("problem")
    timetable = st.session_state.get("generated_timetable")
    result = st.session_state.get("generation_result")

    # 1. KPI Cards Row
    c1, c2, c3, c4, c5, c6 = st.columns(6)

    if problem is not None:
        try:
            sessions = expand_sessions(problem)
            total_sessions = len(sessions)
        except Exception:
            total_sessions = sum(
                req.weekly_sessions
                for g in problem.student_groups
                for req in g.subject_requirements
            )

        with c1:
            render_kpi_card("Classes", len(problem.student_groups), "Student groups")
        with c2:
            render_kpi_card("Faculty", len(problem.teachers), "Qualified instructors")
        with c3:
            render_kpi_card("Subjects", len(problem.subjects), "Theory & Labs")
        with c4:
            render_kpi_card("Rooms", len(problem.rooms), "Classrooms & Labs")
        with c5:
            render_kpi_card("Sessions", total_sessions, "Weekly requirements")
        with c6:
            status_text = "Generated" if timetable is not None else "Ready"
            render_kpi_card("Status", status_text, "Timetable state")
    else:
        with c1:
            render_kpi_card("Classes", "—", "No data")
        with c2:
            render_kpi_card("Faculty", "—", "No data")
        with c3:
            render_kpi_card("Subjects", "—", "No data")
        with c4:
            render_kpi_card("Rooms", "—", "No data")
        with c5:
            render_kpi_card("Sessions", "—", "No data")
        with c6:
            render_kpi_card("Status", "Empty", "Dataset required")

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. Dataset Banner or Empty State
    if problem is None:
        st.info(
            "👋 **Welcome! No dataset is currently loaded.** "
            "To begin scheduling, navigate to **Upload Dataset** in the sidebar or upload a standard institution CSV file.",
            icon="ℹ️",
        )
        col_btn1, _ = st.columns([2, 5])
        with col_btn1:
            if st.button("📁 Go to Dataset Upload", use_container_width=True):
                st.session_state["nav_selection"] = "Upload Dataset"
                st.rerun()
        return

    # 3. Timetable Generation Summary (when dataset is loaded)
    st.subheader("Scheduling System Status")

    col_sum1, col_sum2 = st.columns([3, 2])

    with col_sum1:
        st.markdown(
            f"""
            <div class="academic-card">
                <h4 style="margin-top:0; color:#1e3a8a;">Active Dataset: {st.session_state.get('dataset_name', 'Loaded Dataset')}</h4>
                <p style="color:#64748b; font-size:0.9rem;">
                    Working Days: <strong>{', '.join(problem.time_structure.working_days)}</strong> &bull;
                    Periods/Day: <strong>{problem.time_structure.periods_per_day}</strong> &bull;
                    Period Length: <strong>{problem.time_structure.period_duration_minutes} min</strong>
                </p>
                <div style="margin-top:10px;">
                    {render_badge('Input Verified' if not st.session_state.get('validation_errors') else 'Validation Warnings', 'success' if not st.session_state.get('validation_errors') else 'warning')}
                    {render_badge('Timetable Ready' if timetable is not None else 'Solver Not Executed', 'info' if timetable is not None else 'neutral')}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_sum2:
        if result is not None:
            st.markdown(
                f"""
                <div class="academic-card">
                    <h4 style="margin-top:0; color:#1e3a8a;">Latest Solver Run</h4>
                    <ul style="font-size:0.88rem; color:#334155; padding-left:1.2rem; margin-bottom:0;">
                        <li><strong>Algorithm:</strong> {result.get('algorithm', 'N/A')}</li>
                        <li><strong>Status:</strong> {result.get('status', 'N/A')}</li>
                        <li><strong>Runtime:</strong> {result.get('runtime_seconds', 0.0):.3f}s</li>
                        <li><strong>Scheduled Sessions:</strong> {result.get('scheduled_count', 0)}</li>
                        <li><strong>Unscheduled:</strong> {result.get('unscheduled_count', 0)}</li>
                        <li><strong>Hard Violations:</strong> {result.get('hard_violations', 'N/A')}</li>
                        <li><strong>Soft Penalty:</strong> {result.get('soft_penalty', 'N/A')}</li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class="academic-card">
                    <h4 style="margin-top:0; color:#64748b;">No Solver Run Yet</h4>
                    <p style="font-size:0.88rem; color:#64748b;">
                        A dataset is active and verified. Go to <strong>Generate Timetable</strong> to select an algorithm, inspect CSP domains, and run the solver.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # 4. Quick Links / Action Guide
    st.markdown("### Next Steps")
    q1, q2, q3 = st.columns(3)
    with q1:
        if st.button("📊 View & Manage Data", use_container_width=True):
            st.session_state["nav_selection"] = "Manage Data"
            st.rerun()
    with q2:
        if st.button("⚡ Generate Timetable", use_container_width=True):
            st.session_state["nav_selection"] = "Generate Timetable"
            st.rerun()
    with q3:
        if st.button("🔍 Constraint Verification", use_container_width=True):
            st.session_state["nav_selection"] = "Constraint Validation"
            st.rerun()
