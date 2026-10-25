"""Streamlit interface for Timetable Studio."""

import html
import io
import json
import time
from pathlib import Path

import pandas as pd
import streamlit as st

from src.data.loaders import load_timetable_csv
from src.data.validation import validate_timetable_input
from src.services.scheduler import ALGORITHMS, run_scheduler


APP_VERSION = "1.0"
CONFIG_PATH = Path(__file__).with_name(".timetable_studio.json")
ALGORITHM_NAMES = list(ALGORITHMS)
DEFAULT_SETTINGS = {
    "algorithm": "Heuristic Backtracking",
    "max_steps": 2000,
    "seed": 42,
    "timetable_view": "All Classes",
    "show_teacher": True,
    "show_room": True,
}


def load_settings():
    """Read persisted preferences, falling back safely for missing/bad files."""
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return DEFAULT_SETTINGS.copy()
        settings = DEFAULT_SETTINGS | data
        if settings["algorithm"] not in ALGORITHM_NAMES:
            settings["algorithm"] = DEFAULT_SETTINGS["algorithm"]
        if settings["timetable_view"] not in (
            "All Classes", "Individual Class", "Individual Teacher", "Individual Room"
        ):
            settings["timetable_view"] = DEFAULT_SETTINGS["timetable_view"]
        settings["max_steps"] = max(100, min(20000, int(settings["max_steps"])))
        settings["seed"] = max(0, min(999999, int(settings["seed"])))
        settings["show_teacher"] = bool(settings["show_teacher"])
        settings["show_room"] = bool(settings["show_room"])
        return settings
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return DEFAULT_SETTINGS.copy()


def save_settings(settings):
    """Persist only recognized preference fields."""
    clean = {key: settings[key] for key in DEFAULT_SETTINGS}
    CONFIG_PATH.write_text(json.dumps(clean, indent=2), encoding="utf-8")


def build_schedule_dataframe(timetable, problem):
    subjects = {item.id: item.name for item in problem.subjects}
    teachers = {item.id: item.name for item in problem.teachers}
    groups = {item.id: item.name for item in problem.student_groups}
    rooms = {item.id: item.name for item in problem.rooms}
    rows = []
    seen = set()
    for session in timetable.sessions:
        assignment = session.assignment
        if assignment is None:
            continue
        key = (session.session_id, assignment.day, assignment.start_period)
        if key in seen:
            continue
        seen.add(key)
        rows.append({
            "Class": groups.get(session.group_id, session.group_id),
            "Subject": subjects.get(session.subject_id, session.subject_id),
            "Teacher": teachers.get(assignment.teacher_id, assignment.teacher_id),
            "Room": rooms.get(assignment.room_id, assignment.room_id),
            "Day": str(assignment.day),
            "Start Period": int(assignment.start_period),
            "Duration": int(session.duration_slots),
        })
    columns = ["Class", "Subject", "Teacher", "Room", "Day", "Start Period", "Duration"]
    return pd.DataFrame(rows, columns=columns)


def filtered_export_frame(frame, settings):
    frame = frame.copy()
    if not settings["show_teacher"]:
        frame.drop(columns=["Teacher"], inplace=True, errors="ignore")
    if not settings["show_room"]:
        frame.drop(columns=["Room"], inplace=True, errors="ignore")
    return frame


def weekly_grid(frame, problem, settings):
    """Render simultaneous sessions as separate cards in a weekly grid."""
    days = [str(day) for day in problem.time_structure.working_days]
    period_count = int(problem.time_structure.periods_per_day)
    labels = [f"P{i}" for i in range(1, period_count + 1)]
    slots = {(label, day): [] for label in labels for day in days}
    for _, row in frame.iterrows():
        day = next((d for d in days if d.lower() == str(row.Day).lower()), None)
        if day is None:
            continue
        start, duration = int(row["Start Period"]), int(row.Duration)
        subject = str(row.Subject)
        details = [str(row.Class), subject]
        if settings["show_teacher"]:
            details.append(str(row.Teacher))
        if settings["show_room"]:
            details.append(str(row.Room))
        for period in range(start, start + duration):
            label = f"P{period}"
            if (label, day) not in slots:
                continue
            slots[(label, day)].append(
                details if period == start else [str(row.Class), f"↳ {subject} · cont."]
            )
    break_periods = set()
    for item in problem.time_structure.break_periods or []:
        try:
            break_periods.add(f"P{int(item)}")
        except (ValueError, TypeError):
            continue
    parts = ['<div class="schedule-scroll"><table class="schedule-grid"><thead><tr>',
             '<th class="period-head">Period</th>']
    parts.extend(f'<th>{html.escape(day)}</th>' for day in days)
    parts.append('</tr></thead><tbody>')
    for label in labels:
        parts.append(f'<tr><th class="period-cell">{label}</th>')
        for day in days:
            sessions = slots[(label, day)]
            if sessions:
                cards = []
                for details in sessions:
                    title, *meta = details
                    cards.append(
                        '<div class="session-card">'
                        f'<div class="session-title">{html.escape(title)}</div>'
                        + ''.join(
                            f'<div class="session-meta">{html.escape(item)}</div>'
                            for item in meta
                        )
                        + '</div>'
                    )
                content = ''.join(cards)
            elif label in break_periods:
                content = '<span class="schedule-break">Break</span>'
            else:
                content = '<span class="schedule-empty">—</span>'
            parts.append(f'<td>{content}</td>')
        parts.append('</tr>')
    parts.append('</tbody></table></div>')
    return ''.join(parts)


def export_buttons(frame):
    if frame.empty:
        return
    csv_bytes = frame.to_csv(index=False).encode("utf-8")
    csv_col, excel_col = st.columns(2)
    with csv_col:
        st.download_button("Download filtered CSV", csv_bytes, "timetable.csv", "text/csv", width="stretch")
    with excel_col:
        try:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                frame.to_excel(writer, index=False, sheet_name="Timetable")
            st.download_button(
                "Download filtered Excel", buffer.getvalue(), "timetable.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width="stretch",
            )
        except ImportError:
            st.button("Excel export unavailable", disabled=True, width="stretch")
            st.caption("Install the project dependencies to enable Excel export: pip install -r requirements.txt")


def page_header(title, subtitle):
    st.markdown(f'<div class="page-title">{title}</div><div class="page-subtitle">{subtitle}</div>', unsafe_allow_html=True)


st.set_page_config(page_title="Timetable Studio", page_icon="▦", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
:root{--page:#f6f6f4;--panel:#fff;--sidebar:#ececea;--text:#282826;--muted:#747471;--border:#dededb}
.stApp{background:var(--page);color:var(--text);accent-color:#333}
[data-testid="stHeader"]{background:transparent}
[data-testid="stSidebar"]{background:var(--sidebar);border-right:1px solid var(--border)}
.block-container{max-width:1450px;padding:2.4rem 3rem 4rem}
.brand{font-size:21px;font-weight:750;letter-spacing:-.6px;color:var(--text)}
.brand-subtitle{color:var(--muted);font-size:12px;margin:5px 0 32px}
.page-title{font-size:30px;font-weight:750;letter-spacing:-1px;margin-bottom:5px}
.page-subtitle{color:var(--muted);font-size:14px;margin-bottom:26px}
.panel-heading{font-size:16px;font-weight:700;margin-bottom:5px}
.panel-description{color:var(--muted);font-size:13px;margin-bottom:16px}
div[data-testid="stVerticalBlockBorderWrapper"]{background:var(--panel);border:1px solid var(--border);border-radius:12px}
.stButton>button,.stDownloadButton>button{background:#e7e7e4!important;color:#292929!important;border:1px solid #d2d2cf!important;border-radius:8px!important;transition:all .18s ease}
.stButton>button:hover,.stDownloadButton>button:hover{background:#d4d4d0!important;border-color:#bdbdb9!important}
.stSelectbox div[data-baseweb="select"]>div,.stNumberInput input,.stTextInput input{background:#fff!important;color:#292929!important;border-color:#d2d2cf!important}
[data-testid="stAlert"]{background:#ededeb!important;border:1px solid #d2d2cf!important;color:#292929!important;border-radius:8px}
[data-testid="stAlert"] p,[data-testid="stAlert"] div,[data-testid="stAlert"] svg{color:#292929!important;fill:#292929!important}
[data-testid="stMetricLabel"]{color:#747471!important}[data-testid="stMetricValue"]{color:#292929!important}
[data-testid="stDataFrame"]{border:1px solid var(--border);border-radius:8px}
.schedule-scroll{overflow-x:auto;border:1px solid var(--border);border-radius:9px;background:#fff}
.schedule-grid{width:100%;min-width:720px;table-layout:fixed;border-collapse:collapse;font-size:12px}
.schedule-grid th,.schedule-grid td{border-right:1px solid #e5e5e2;border-bottom:1px solid #e5e5e2;padding:7px;vertical-align:top;overflow-wrap:anywhere}
.schedule-grid thead th{background:#f1f1ef;color:#383836;text-align:left;font-weight:650;height:36px}
.schedule-grid .period-head,.schedule-grid .period-cell{width:68px;background:#f7f7f5;color:#5f5f5b;font-weight:650}
.schedule-grid td{height:68px}
.session-card{padding:6px 7px;margin:0 0 5px;background:#f3f3f1;border:1px solid #e0e0dd;border-radius:6px;line-height:1.3}
.session-title{font-weight:650;color:#292927;margin-bottom:3px}
.session-meta{font-size:11px;color:#666661}
.schedule-break,.schedule-empty{display:inline-block;padding:5px 6px;color:#858580;font-size:11px}
.schedule-break{background:#f1f1ef;border:1px solid #e1e1de;border-radius:5px;color:#555550;font-weight:600}
hr{border-color:var(--border)}
</style>
""", unsafe_allow_html=True)

if "settings" not in st.session_state:
    st.session_state.settings = load_settings()
for key, value in {
    "csv_bytes": None, "csv_name": None, "problem": None, "result": None,
    "schedule_df": None, "validation_errors": [], "generation_status": "No timetable generated.",
}.items():
    if key not in st.session_state:
        st.session_state[key] = value

with st.sidebar:
    st.markdown('<div class="brand">◈ Timetable Studio</div><div class="brand-subtitle">Academic scheduling workspace</div>', unsafe_allow_html=True)
    page = st.radio("Navigation", ["Dashboard", "Timetable", "Settings", "About"], key="navigation", label_visibility="collapsed")
    st.divider()
    st.caption(f"TIMETABLE STUDIO · v{APP_VERSION}")

settings = st.session_state.settings

if page == "Dashboard":
    page_header("Dashboard", "Load your scheduling data and check workspace status.")
    with st.container(border=True):
        st.markdown('<div class="panel-heading">Upload and validate input</div><div class="panel-description">Select the timetable CSV, then load it into the workspace.</div>', unsafe_allow_html=True)
        upload = st.file_uploader("Choose a CSV file", type=["csv"], key="dashboard_upload")
        if upload is not None:
            st.session_state.csv_bytes = upload.getvalue()
            st.session_state.csv_name = upload.name
        if st.session_state.csv_name:
            st.caption(f"Selected file: {st.session_state.csv_name}")
        if st.button("Load and validate data", disabled=not st.session_state.csv_bytes):
            try:
                problem, report = load_timetable_csv(io.BytesIO(st.session_state.csv_bytes), return_report=True)
                errors = validate_timetable_input(problem)
                st.session_state.problem = problem
                st.session_state.validation_errors = errors
                st.session_state.result = None
                st.session_state.schedule_df = None
                st.session_state.generation_status = "Ready to generate." if not errors else "Input validation needs attention."
                if errors:
                    st.error("Input loaded with validation issues.")
                else:
                    st.success("Input loaded and validated.")
                if report:
                    with st.expander("Input preprocessing summary"):
                        st.json(report)
            except Exception as error:
                st.session_state.problem = None
                st.session_state.validation_errors = [str(error)]
                st.error(f"Could not load this CSV: {error}")
        if st.session_state.validation_errors:
            with st.expander("Validation details", expanded=True):
                for error in st.session_state.validation_errors:
                    st.write(f"• {error}")
    problem = st.session_state.problem
    if problem:
        with st.container(border=True):
            st.markdown('<div class="panel-heading">Loaded data</div>', unsafe_allow_html=True)
            cols = st.columns(4)
            for col, label, value in zip(cols, ["Classes", "Subjects", "Teachers", "Rooms"], [len(problem.student_groups), len(problem.subjects), len(problem.teachers), len(problem.rooms)]):
                col.metric(label, value)
            st.caption(f"{len(problem.time_structure.working_days)} working days · {problem.time_structure.periods_per_day} periods per day · Source: {st.session_state.csv_name or 'loaded CSV'}")
    if problem:
        with st.container(border=True):
            st.markdown('<div class="panel-heading">Generate timetable</div><div class="panel-description">Runs the solver and limits saved in Settings.</div>', unsafe_allow_html=True)
            st.caption(f"{settings['algorithm']} · {settings['max_steps']:,} maximum steps · random seed {settings['seed']}")
            if st.button("Generate timetable", type="primary", disabled=bool(st.session_state.validation_errors), width="stretch"):
                start = time.perf_counter()
                st.session_state.generation_status = f"Running {settings['algorithm']}…"
                try:
                    result = run_scheduler(
                        problem,
                        algorithm=settings["algorithm"],
                        max_steps=settings["max_steps"],
                        seed=settings["seed"],
                    )
                    result["runtime_seconds"] = round(time.perf_counter() - start, 4)
                    st.session_state.result = result
                    if result["success"]:
                        st.session_state.schedule_df = build_schedule_dataframe(result["timetable"], problem)
                        st.session_state.generation_status = f"Valid timetable generated with {settings['algorithm']}."
                    else:
                        st.session_state.schedule_df = None
                        st.session_state.generation_status = result["message"]
                except Exception as error:
                    st.session_state.result = {
                        "success": False, "message": str(error), "violations": [],
                        "stats": {}, "runtime_seconds": round(time.perf_counter() - start, 4),
                    }
                    st.session_state.schedule_df = None
                    st.session_state.generation_status = f"Generation failed: {error}"
                st.rerun()
    with st.container(border=True):
        st.markdown('<div class="panel-heading">Latest run</div>', unsafe_allow_html=True)
        st.write(st.session_state.generation_status)
        result = st.session_state.result
        if result:
            (st.success if result["success"] else st.error)(result["message"])
            stats = result.get("stats", {})
            metric_values = [
                (key, value) for key, value in stats.items()
                if isinstance(value, (int, float))
            ] + [("runtime_seconds", result.get("runtime_seconds", "—"))]
            if metric_values:
                columns = st.columns(min(4, len(metric_values)))
                for index, (label, value) in enumerate(metric_values):
                    columns[index % len(columns)].metric(label.replace("_", " ").title(), value)
            detail_stats = {key: value for key, value in stats.items() if not isinstance(value, (int, float))}
            if detail_stats:
                with st.expander("Detailed solver statistics"):
                    st.json(detail_stats)
            if result.get("violations"):
                st.markdown("**Timetable validation issues**")
                for item in result["violations"]:
                    st.write(f"• {item}")
            if result.get("penalties"):
                st.markdown("**Quality metrics**")
                cols = st.columns(len(result["penalties"]))
                for col, (name, value) in zip(cols, result["penalties"].items()):
                    col.metric(name.replace("_", " ").title(), value)
    with st.container(border=True):
        st.markdown('<div class="panel-heading">Timetable preview</div><div class="panel-description">A compact preview of the current workspace schedule.</div>', unsafe_allow_html=True)
        if st.session_state.schedule_df is not None and not st.session_state.schedule_df.empty:
            st.dataframe(st.session_state.schedule_df.head(8), width="stretch", hide_index=True)
        else:
            st.caption("No timetable exists yet. Load data and generate a schedule here.")

elif page == "Timetable":
    page_header("Timetable", "Explore the generated schedule through one shared weekly calendar.")
    df, problem = st.session_state.schedule_df, st.session_state.problem
    if df is None or df.empty or problem is None:
        st.info("No timetable generated yet. Load input and run the scheduler from Dashboard.")
    else:
        view_options = ["All Classes", "Individual Class", "Individual Teacher", "Individual Room"]
        default_view = settings["timetable_view"]
        view = st.selectbox("View", view_options, index=view_options.index(default_view), key="active_timetable_view")
        filtered = df.copy()
        selected = view
        filter_column = {"Individual Class": "Class", "Individual Teacher": "Teacher", "Individual Room": "Room"}.get(view)
        if filter_column:
            selected = st.selectbox(f"Select {filter_column.lower()}", sorted(df[filter_column].dropna().unique().tolist()), key=f"filter_{filter_column.lower()}")
            filtered = filtered[filtered[filter_column] == selected]
        export_frame = filtered_export_frame(filtered, settings)
        with st.container(border=True):
            st.markdown(f'<div class="panel-heading">Weekly schedule · {selected}</div>', unsafe_allow_html=True)
            st.markdown(weekly_grid(filtered, problem, settings), unsafe_allow_html=True)
            st.caption("Multi-period sessions appear once with continuation markers. Break periods are labelled when empty.")
            st.divider()
            st.markdown("**Exports**")
            export_buttons(export_frame)
            with st.expander(f"Session list · {len(export_frame)} sessions"):
                st.dataframe(export_frame.sort_values(["Day", "Start Period"], kind="stable"), width="stretch", hide_index=True)

elif page == "Settings":
    page_header("Settings", "Choose defaults and display details for this workspace.")
    with st.container(border=True):
        st.markdown('<div class="panel-heading">Workspace preferences</div><div class="panel-description">Preferences save to a small local configuration file and apply across pages.</div>', unsafe_allow_html=True)
        algorithm = st.selectbox("Default scheduling algorithm", ALGORITHM_NAMES, index=ALGORITHM_NAMES.index(settings["algorithm"]), key="setting_algorithm")
        steps = st.number_input("Default maximum solver steps", min_value=100, max_value=20000, step=100, value=settings["max_steps"], key="setting_steps")
        seed = st.number_input("Default random seed", min_value=0, max_value=999999, step=1, value=settings["seed"], key="setting_seed")
        view_options = ["All Classes", "Individual Class", "Individual Teacher", "Individual Room"]
        view = st.selectbox("Default timetable view", view_options, index=view_options.index(settings["timetable_view"]), key="setting_view")
        show_teacher = st.checkbox("Show teacher details", value=settings["show_teacher"], key="setting_teacher")
        show_room = st.checkbox("Show room details", value=settings["show_room"], key="setting_room")
        updated = {"algorithm": algorithm, "max_steps": int(steps), "seed": int(seed), "timetable_view": view, "show_teacher": show_teacher, "show_room": show_room}
        if updated != settings:
            try:
                save_settings(updated)
                st.session_state.settings = updated
                # Streamlit retains widget state across page navigation.
                st.session_state["active_timetable_view"] = view
                st.success("Settings saved.")
            except OSError as error:
                st.error(f"Could not save settings: {error}")

elif page == "About":
    page_header("About", "Application details.")
    with st.container(border=True):
        st.markdown('<div class="panel-heading">Timetable Studio</div>', unsafe_allow_html=True)
        st.write(f"Version {APP_VERSION}")
        st.write("A scheduling workspace for organising classes, teachers, subjects and rooms with constraint-based algorithms and timetable quality metrics.")
