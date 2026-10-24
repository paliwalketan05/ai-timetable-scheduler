"""Timetable Scheduler - Streamlit Application.

A clean, polished, single-page academic interface for:
- Uploading CSV datasets and downloading templates
- Selecting scheduling algorithms
- Generating conflict-free timetables
- Viewing schedules by Class, Teacher, or Room
- Validating constraints
- Exporting to CSV and Excel
"""

import importlib
import io
import time
import streamlit as st
import pandas as pd

from src.models.entities import SchedulingProblem
from src.models.schedule import Timetable, ScheduledSession
from src.data.loaders import load_timetable_csv
from src.data.validation import validate_timetable_input
from src.csp.sessions import expand_sessions
from src.csp.domains import generate_domains
from src.ui.styles import apply_academic_theme, render_badge
from src.ui.state import (
    init_session_state,
    set_loaded_dataset,
    clear_loaded_dataset,
    set_timetable_result,
)
from src.ui.views.generate import check_algorithm_implementation, ALGORITHMS
from src.ui.views.validation import check_validator_module, HARD_CONSTRAINTS
from src.ui.views.export import generate_export_dataframe

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

# 1. Page Configuration
st.set_page_config(
    page_title="Timetable Scheduler",
    page_icon="📅",
    layout="centered",
    initial_sidebar_state="collapsed",
)

apply_academic_theme()
init_session_state()

# 2. Top-Centered Header
st.markdown(
    """
    <div class="academic-header">
        <h1 class="academic-title">Timetable Scheduler</h1>
        <p class="academic-subtitle">
            Generate conflict-free academic timetables using constraint satisfaction algorithms.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Section: Upload Dataset
# -----------------------------------------------------------------------------
st.markdown('<div class="section-header">Upload Dataset</div>', unsafe_allow_html=True)

col_upload, col_template = st.columns([3, 1], gap="medium")

with col_upload:
    uploaded_file = st.file_uploader(
        "Upload CSV Dataset",
        type=["csv"],
        help="Upload an institution CSV dataset matching the project schema.",
        label_visibility="collapsed",
    )

with col_template:
    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
    st.download_button(
        label="Download CSV Template",
        data=CSV_TEMPLATE,
        file_name="timetable_template.csv",
        mime="text/csv",
        use_container_width=True,
    )

# Handle Data Ingestion
if uploaded_file is not None:
    try:
        problem, prep_report = load_timetable_csv(uploaded_file, return_report=True)
        if hasattr(uploaded_file, "seek"):
            uploaded_file.seek(0)
        raw_df = pd.read_csv(uploaded_file, dtype=str)
        val_errors = validate_timetable_input(problem)
        set_loaded_dataset(problem, raw_df, prep_report, val_errors, uploaded_file.name)
        st.markdown(
            f"""
            <div class="academic-alert academic-alert-success">
                Loaded dataset: <strong>{uploaded_file.name}</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )
    except Exception as exc:
        st.markdown(
            f"""
            <div class="academic-alert academic-alert-error">
                Failed to load CSV: {exc}
            </div>
            """,
            unsafe_allow_html=True,
        )

# Active dataset display
problem: SchedulingProblem | None = st.session_state.get("problem")
raw_df: pd.DataFrame | None = st.session_state.get("raw_dataframe")
val_errors: list[str] = st.session_state.get("validation_errors", [])

if problem is not None and raw_df is not None:
    col_meta, col_btn = st.columns([4, 1])
    with col_meta:
        st.markdown(
            f"""
            <div style="font-size: 0.85rem; color: #73796F; padding: 4px 0;">
                Active: <strong style="color: #252B25;">{st.session_state.get('dataset_name')}</strong> &bull;
                {len(problem.subjects)} Subjects, {len(problem.teachers)} Faculty,
                {len(problem.student_groups)} Cohorts, {len(problem.rooms)} Rooms,
                {len(problem.time_structure.working_days)} Working Days
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_btn:
        if st.button("Reset Data", use_container_width=True):
            clear_loaded_dataset()
            st.rerun()

    # Compact data preview
    with st.expander("Dataset Preview", expanded=False):
        st.dataframe(raw_df.head(6), use_container_width=True)

    # Validation errors or success
    if val_errors:
        st.markdown(
            f"""
            <div class="academic-alert academic-alert-error">
                <strong>Validation Issues Detected ({len(val_errors)}):</strong><br>
                {'<br>'.join(f'&bull; {err}' for err in val_errors)}
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="academic-alert academic-alert-success" style="padding: 6px 12px; margin-top: 4px; font-size: 0.84rem;">
                ✓ Input consistency, capacity bounds, and reference checks verified.
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("<hr>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Section: Select Scheduling Algorithm
# -----------------------------------------------------------------------------
st.markdown('<div class="section-header">Select Scheduling Algorithm</div>', unsafe_allow_html=True)

algo_keys = list(ALGORITHMS.keys())
algo_options = [ALGORITHMS[k]["name"] for k in algo_keys]

selected_name = st.selectbox(
    "Select Scheduling Algorithm",
    algo_options,
    index=0,
    label_visibility="collapsed",
)

selected_key = next(k for k in algo_keys if ALGORITHMS[k]["name"] == selected_name)
algo_info = ALGORITHMS[selected_key]
is_implemented = check_algorithm_implementation(algo_info["module"])

if not is_implemented:
    st.markdown(
        f"""
        <div class="academic-alert academic-alert-warning">
            <strong>Algorithm Not Available:</strong> The solver logic in <code>{algo_info['module']}</code> is currently
            an incomplete placeholder. Only implemented algorithms can be executed.
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<hr>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Section: Generate Timetable
# -----------------------------------------------------------------------------
st.markdown('<div class="section-header">Generate Timetable</div>', unsafe_allow_html=True)

generate_clicked = st.button("Generate Timetable", type="primary", use_container_width=True)

if generate_clicked:
    if problem is None:
        st.markdown(
            """
            <div class="academic-alert academic-alert-warning">
                Please upload a CSV dataset before generating a timetable.
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif val_errors:
        st.markdown(
            """
            <div class="academic-alert academic-alert-error">
                Cannot generate timetable: The uploaded dataset contains validation errors. Please correct your CSV file.
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        try:
            sessions = expand_sessions(problem)
            domains = generate_domains(problem, sessions)
            empty_domains = [s.id for s in sessions if len(domains.get(s.id, [])) == 0]

            if empty_domains:
                st.markdown(
                    f"""
                    <div class="academic-alert academic-alert-error">
                        <strong>Infeasible Problem:</strong> {len(empty_domains)} session(s) have 0 candidate time/room slots.
                        Check teacher availability or room capacities for: {', '.join(empty_domains[:3])}.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            elif not is_implemented:
                st.markdown(
                    f"""
                    <div class="academic-alert academic-alert-info">
                        <strong>Solver Implementation Pending:</strong> The selected algorithm <code>{algo_info['name']}</code>
                        in <code>{algo_info['module']}</code> is currently a placeholder without a callable <code>solve()</code> function.
                        Session expansion ({len(sessions)} sessions) and domain generation were verified,
                        but search execution requires finishing the backend solver module.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                with st.spinner(f"Executing {algo_info['name']}..."):
                    start_time = time.perf_counter()
                    mod = importlib.import_module(algo_info["module"])
                    solve_func = getattr(mod, "solve", None) or getattr(mod, "solve_timetable", None)

                    timetable, metrics = solve_func(
                        problem,
                        time_limit=15,
                        max_iterations=5000,
                        seed=42,
                    )
                    runtime = time.perf_counter() - start_time

                    result_payload = {
                        "algorithm": algo_info["name"],
                        "status": "Success" if timetable is not None else "No Solution Found",
                        "runtime_seconds": runtime,
                        "scheduled_count": len(timetable.sessions) if timetable else 0,
                        "unscheduled_count": len(sessions) - (len(timetable.sessions) if timetable else 0),
                        "hard_violations": metrics.get("hard_violations", 0) if isinstance(metrics, dict) else 0,
                        "soft_penalty": metrics.get("soft_penalty", 0) if isinstance(metrics, dict) else 0,
                    }
                    set_timetable_result(timetable, result_payload)

                    if timetable:
                        st.markdown(
                            f"""
                            <div class="academic-alert academic-alert-success">
                                Timetable generated successfully in {runtime:.3f} seconds!
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            """
                            <div class="academic-alert academic-alert-error">
                                No conflict-free timetable could be found within the allotted search budget.
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                    st.rerun()

        except Exception as exc:
            st.markdown(
                f"""
                <div class="academic-alert academic-alert-error">
                    Error during timetable generation: {exc}
                </div>
                """,
                unsafe_allow_html=True,
            )

# -----------------------------------------------------------------------------
# Section: Results (Generated Timetable, Validation, Export - ONLY when timetable exists)
# -----------------------------------------------------------------------------
timetable: Timetable | None = st.session_state.get("generated_timetable")

if timetable is not None and problem is not None:
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">Generated Timetable</div>', unsafe_allow_html=True)

    subjects_map = {s.id: s.name for s in problem.subjects}
    teachers_map = {t.id: t.name for t in problem.teachers}
    rooms_map = {r.id: r.name for r in problem.rooms}
    groups_map = {g.id: g for g in problem.student_groups}

    working_days = problem.time_structure.working_days
    periods_per_day = problem.time_structure.periods_per_day
    break_periods = set(problem.time_structure.break_periods)

    col_view_type, col_entity_select = st.columns([1, 2])
    with col_view_type:
        filter_mode = st.radio("View by:", ["Class", "Teacher", "Room"], horizontal=True)

    with col_entity_select:
        if filter_mode == "Class":
            c_options = [g.id for g in problem.student_groups]
            c_label = lambda cid: f"{cid} - {groups_map[cid].name}" if cid in groups_map else cid
            selected_entity = st.selectbox("Select Class", c_options, format_func=c_label)
        elif filter_mode == "Teacher":
            t_options = [t.id for t in problem.teachers]
            t_label = lambda tid: f"{tid} - {teachers_map.get(tid, tid)}"
            selected_entity = st.selectbox("Select Teacher", t_options, format_func=t_label)
        else:
            r_options = [r.id for r in problem.rooms]
            r_label = lambda rid: f"{rid} - {rooms_map.get(rid, rid)}"
            selected_entity = st.selectbox("Select Room", r_options, format_func=r_label)

    # Collect relevant sessions
    relevant_sessions: list[ScheduledSession] = []
    for s in timetable.sessions:
        asgn = s.assignment
        if filter_mode == "Class" and s.group_id == selected_entity:
            relevant_sessions.append(s)
        elif filter_mode == "Teacher" and asgn.teacher_id == selected_entity:
            relevant_sessions.append(s)
        elif filter_mode == "Room" and asgn.room_id == selected_entity:
            relevant_sessions.append(s)

    class_lunch_periods = set()
    if filter_mode == "Class" and selected_entity in groups_map:
        class_lunch_periods = set(groups_map[selected_entity].lunch_break_periods)

    # Build Grid mapping
    grid = {p: {d: [] for d in working_days} for p in range(1, periods_per_day + 1)}
    for s in relevant_sessions:
        asgn = s.assignment
        start_p = asgn.start_period
        duration = s.duration_slots
        day = asgn.day
        for offset in range(duration):
            p = start_p + offset
            if p in grid and day in grid[p]:
                grid[p][day].append({
                    "subject": subjects_map.get(s.subject_id, s.subject_id),
                    "teacher": teachers_map.get(asgn.teacher_id, asgn.teacher_id),
                    "room": rooms_map.get(asgn.room_id, asgn.room_id),
                    "class": groups_map[s.group_id].name if s.group_id in groups_map else s.group_id,
                    "is_continuation": offset > 0,
                    "duration": duration,
                })

    # Render HTML grid
    header_th = "".join(f"<th>{d}</th>" for d in working_days)
    body_rows = []
    for p in range(1, periods_per_day + 1):
        is_break = p in break_periods
        is_lunch = p in class_lunch_periods
        cells = [f"<td class='academic-tt-period-col'>P{p}</td>"]

        for d in working_days:
            slot_items = grid[p][d]
            if is_break:
                cell_html = "<div class='academic-break-cell'>Break</div>"
            elif is_lunch:
                cell_html = "<div class='academic-lunch-cell'>Lunch Break</div>"
            elif not slot_items:
                cell_html = "<div class='academic-empty-cell'>—</div>"
            else:
                item = slot_items[0]
                if item["is_continuation"]:
                    cell_html = f"<div class='academic-session-cell' style='border-left:3px dashed #82977A; opacity:0.85;'><div class='academic-session-subj' style='font-size:0.75rem; color:#73796F;'>↳ {item['subject']} (Cont.)</div></div>"
                else:
                    if filter_mode == "Class":
                        subline = f"{item['teacher']} &bull; {item['room']}"
                    elif filter_mode == "Teacher":
                        subline = f"{item['class']} &bull; {item['room']}"
                    else:
                        subline = f"{item['class']} &bull; {item['teacher']}"
                    lab_tag = f"<span class='academic-lab-badge'>Lab ({item['duration']}h)</span>" if item["duration"] > 1 else ""
                    cell_html = f"""
                    <div class='academic-session-cell'>
                        <div class='academic-session-subj'>{item['subject']}{lab_tag}</div>
                        <div class='academic-session-meta'>{subline}</div>
                    </div>
                    """
            cells.append(f"<td>{cell_html}</td>")
        body_rows.append(f"<tr>{''.join(cells)}</tr>")

    st.markdown(
        f"""
        <table class="academic-tt-table">
            <thead>
                <tr>
                    <th style="width:70px;">Period</th>
                    {header_th}
                </tr>
            </thead>
            <tbody>
                {''.join(body_rows)}
            </tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )

    # Compact Table View
    with st.expander("Compact Table View (All Scheduled Sessions)", expanded=False):
        table_rows = []
        for s in timetable.sessions:
            asgn = s.assignment
            p_label = f"P{asgn.start_period}" if s.duration_slots == 1 else f"P{asgn.start_period}-P{asgn.start_period + s.duration_slots - 1}"
            table_rows.append({
                "Class": groups_map[s.group_id].name if s.group_id in groups_map else s.group_id,
                "Subject": subjects_map.get(s.subject_id, s.subject_id),
                "Teacher": teachers_map.get(asgn.teacher_id, asgn.teacher_id),
                "Room": rooms_map.get(asgn.room_id, asgn.room_id),
                "Day": asgn.day,
                "Period": p_label,
                "Duration": f"{s.duration_slots} slot(s)",
            })
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True)

    # -------------------------------------------------------------------------
    # Section: Constraint Validation
    # -----------------------------------------------------------------------------
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">Constraint Validation</div>', unsafe_allow_html=True)

    validator_func = check_validator_module()

    val_res = {}
    if validator_func is not None:
        try:
            val_res = validator_func(problem, timetable)
        except Exception:
            val_res = {}

    v_table = []
    for hc in HARD_CONSTRAINTS:
        cid = hc["id"]
        if validator_func is None:
            status = "Not Checked"
            violations = "N/A"
            details = "Independent validator module pending in src/evaluation/validator.py"
        else:
            r = val_res.get(cid)
            if r is None:
                status = "Not Checked"
                violations = "N/A"
                details = "Constraint not evaluated"
            elif isinstance(r, dict):
                v_count = r.get("violations", 0)
                violations = str(v_count)
                status = "Passed" if v_count == 0 else "Failed"
                details = r.get("explanation", "")
            else:
                status = "Passed" if r else "Failed"
                violations = "0" if r else "Violated"
                details = ""

        v_table.append({
            "Constraint": cid,
            "Rule": hc["name"],
            "Description": hc["description"],
            "Status": status,
            "Violations": violations,
            "Details": details,
        })

    st.dataframe(pd.DataFrame(v_table), use_container_width=True)

    # -------------------------------------------------------------------------
    # Section: Export Timetable
    # -----------------------------------------------------------------------------
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">Export Timetable</div>', unsafe_allow_html=True)

    export_df = generate_export_dataframe(problem, timetable)
    col_dl_csv, col_dl_xlsx = st.columns(2)

    with col_dl_csv:
        csv_bytes = export_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download CSV",
            data=csv_bytes,
            file_name="generated_timetable.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col_dl_xlsx:
        try:
            xlsx_buf = io.BytesIO()
            with pd.ExcelWriter(xlsx_buf, engine="openpyxl") as writer:
                export_df.to_excel(writer, index=False, sheet_name="Timetable")
            st.download_button(
                label="Download Excel (.xlsx)",
                data=xlsx_buf.getvalue(),
                file_name="generated_timetable.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        except Exception as exc:
            st.caption(f"Excel export unavailable: {exc}")
