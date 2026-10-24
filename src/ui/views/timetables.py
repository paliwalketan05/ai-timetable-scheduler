"""Timetable grid and tabular visualization for classes, teachers, and rooms."""

import streamlit as st
import pandas as pd
from typing import Literal

from src.models.entities import SchedulingProblem
from src.models.schedule import Timetable, ScheduledSession


def render_timetable_view(view_mode: Literal["class", "teacher", "room"]):
    titles = {
        "class": ("Class & Batch Timetables", "Filter schedules by student cohort or batch."),
        "teacher": ("Teacher & Faculty Timetables", "Filter individual faculty teaching schedules."),
        "room": ("Room & Venue Timetables", "Check room occupancy, lab allocations, and free periods."),
    }
    title, subtitle = titles[view_mode]

    st.markdown(
        f"""
        <div class="page-header">
            <h1 class="page-title">{title}</h1>
            <p class="page-subtitle">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    problem: SchedulingProblem | None = st.session_state.get("problem")
    timetable: Timetable | None = st.session_state.get("generated_timetable")

    if problem is None:
        st.warning("⚠️ No dataset is loaded. Please upload a dataset first.")
        if st.button("📁 Go to Upload Dataset"):
            st.session_state["nav_selection"] = "Upload Dataset"
            st.rerun()
        return

    if timetable is None:
        st.info(
            "ℹ️ **No timetable has been generated yet.**\n\n"
            "To view schedules by class, teacher, or room, navigate to **Generate Timetable** and execute a solver.",
            icon="📅",
        )
        if st.button("⚡ Go to Generate Timetable"):
            st.session_state["nav_selection"] = "Generate Timetable"
            st.rerun()
        return

    # Entity maps for quick lookups
    subjects_map = {s.id: s.name for s in problem.subjects}
    teachers_map = {t.id: t.name for t in problem.teachers}
    rooms_map = {r.id: r.name for r in problem.rooms}
    groups_map = {g.id: g for g in problem.student_groups}

    working_days = problem.time_structure.working_days
    periods_per_day = problem.time_structure.periods_per_day
    break_periods = set(problem.time_structure.break_periods)

    # Filter selector based on view_mode
    if view_mode == "class":
        options = [g.id for g in problem.student_groups]
        label_func = lambda gid: f"{gid} - {groups_map[gid].name}" if gid in groups_map else gid
        sel_label = "Select Class / Student Group:"
    elif view_mode == "teacher":
        options = [t.id for t in problem.teachers]
        label_func = lambda tid: f"{tid} - {teachers_map.get(tid, tid)}"
        sel_label = "Select Teacher / Faculty Member:"
    else:  # room
        options = [r.id for r in problem.rooms]
        label_func = lambda rid: f"{rid} - {rooms_map.get(rid, rid)}"
        sel_label = "Select Room / Laboratory:"

    if not options:
        st.warning(f"No {view_mode} entities found in current dataset.")
        return

    selected_id = st.selectbox(sel_label, options, format_func=label_func)

    # Collect relevant sessions for this selected entity
    relevant_sessions: list[ScheduledSession] = []
    for s in timetable.sessions:
        asgn = s.assignment
        if view_mode == "class" and s.group_id == selected_id:
            relevant_sessions.append(s)
        elif view_mode == "teacher" and asgn.teacher_id == selected_id:
            relevant_sessions.append(s)
        elif view_mode == "room" and asgn.room_id == selected_id:
            relevant_sessions.append(s)

    # Class-specific lunch break if viewing class
    class_lunch_periods = set()
    if view_mode == "class" and selected_id in groups_map:
        class_lunch_periods = set(groups_map[selected_id].lunch_break_periods)

    # Grid mapping: grid[period][day] = list of display strings or metadata
    # Periods are 1-indexed
    grid: dict[int, dict[str, list[dict]]] = {
        p: {d: [] for d in working_days} for p in range(1, periods_per_day + 1)
    }

    for s in relevant_sessions:
        asgn = s.assignment
        start_p = asgn.start_period
        duration = s.duration_slots
        day = asgn.day

        for offset in range(duration):
            p = start_p + offset
            if p in grid and day in grid[p]:
                grid[p][day].append(
                    {
                        "session_id": s.session_id,
                        "subject_name": subjects_map.get(s.subject_id, s.subject_id),
                        "subject_id": s.subject_id,
                        "teacher_name": teachers_map.get(asgn.teacher_id, asgn.teacher_id),
                        "room_name": rooms_map.get(asgn.room_id, asgn.room_id),
                        "group_name": groups_map[s.group_id].name if s.group_id in groups_map else s.group_id,
                        "is_continuation": offset > 0,
                        "duration": duration,
                    }
                )

    # Render Visual Timetable Grid
    st.markdown("### Weekly Timetable Grid")

    # Build HTML table for the grid
    header_html = "".join(f"<th style='padding:10px; background-color:#1e3a8a; color:#ffffff; text-align:center;'>{day}</th>" for day in working_days)
    rows_html = []

    for p in range(1, periods_per_day + 1):
        is_break = p in break_periods
        is_lunch = p in class_lunch_periods

        row_cells = [f"<td style='padding:8px; font-weight:600; text-align:center; background-color:#f1f5f9; color:#334155;'>Period {p}</td>"]

        for day in working_days:
            cell_items = grid[p][day]

            if is_break:
                cell_content = "<div class='tt-break'>Institutional Break</div>"
            elif is_lunch:
                cell_content = "<div class='tt-break' style='color:#b45309; border-color:#fde68a;'>Lunch Break</div>"
            elif not cell_items:
                cell_content = "<div class='tt-empty'>—</div>"
            else:
                item = cell_items[0]
                if item["is_continuation"]:
                    cell_content = f"""
                    <div class='tt-cell' style='border-left:3px dashed #3b82f6; opacity:0.85;'>
                        <div class='tt-subject' style='font-size:0.75rem; color:#475569;'>↳ {item['subject_name']} (Cont.)</div>
                    </div>
                    """
                else:
                    second_line = ""
                    if view_mode == "class":
                        second_line = f"👤 {item['teacher_name']} &bull; 🏛️ {item['room_name']}"
                    elif view_mode == "teacher":
                        second_line = f"👥 {item['group_name']} &bull; 🏛️ {item['room_name']}"
                    else:  # room
                        second_line = f"👥 {item['group_name']} &bull; 👤 {item['teacher_name']}"

                    badge = f"<span style='font-size:0.68rem; background:#dbeafe; color:#1e40af; padding:1px 4px; border-radius:3px;'>Lab ({item['duration']} hrs)</span>" if item['duration'] > 1 else ""

                    cell_content = f"""
                    <div class='tt-cell'>
                        <div class='tt-subject'>{item['subject_name']} {badge}</div>
                        <div class='tt-meta'>{second_line}</div>
                    </div>
                    """

            row_cells.append(f"<td style='padding:6px; vertical-align:top;'>{cell_content}</td>")

        rows_html.append(f"<tr>{''.join(row_cells)}</tr>")

    full_table_html = f"""
    <div style='overflow-x:auto; margin-bottom:20px; border-radius:8px; border:1px solid #e2e8f0;'>
        <table style='width:100%; border-collapse:collapse; background-color:#ffffff;'>
            <thead>
                <tr>
                    <th style='padding:10px; background-color:#0f172a; color:#ffffff; width:90px; text-align:center;'>Period</th>
                    {header_html}
                </tr>
            </thead>
            <tbody>
                {''.join(rows_html)}
            </tbody>
        </table>
    </div>
    """
    st.markdown(full_table_html, unsafe_allow_html=True)

    # 2. Tabular Detailed View
    st.markdown("### Scheduled Sessions Table")
    if relevant_sessions:
        table_records = []
        for s in relevant_sessions:
            asgn = s.assignment
            table_records.append(
                {
                    "Session ID": s.session_id,
                    "Class": groups_map[s.group_id].name if s.group_id in groups_map else s.group_id,
                    "Subject": subjects_map.get(s.subject_id, s.subject_id),
                    "Teacher": teachers_map.get(asgn.teacher_id, asgn.teacher_id),
                    "Room": rooms_map.get(asgn.room_id, asgn.room_id),
                    "Day": asgn.day,
                    "Start Period": f"P{asgn.start_period}",
                    "Duration": f"{s.duration_slots} period(s)",
                    "End Period": f"P{asgn.start_period + s.duration_slots - 1}",
                }
            )
        st.dataframe(pd.DataFrame(table_records), use_container_width=True)
    else:
        st.info(f"No sessions currently scheduled for {label_func(selected_id)}.")
