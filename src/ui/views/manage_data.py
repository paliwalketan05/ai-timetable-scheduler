"""Manage Data view displaying structured, tabbed tables of loaded academic entities."""

import streamlit as st
import pandas as pd


def render_manage_data_page():
    st.markdown(
        """
        <div class="page-header">
            <h1 class="page-title">Manage Academic Data</h1>
            <p class="page-subtitle">Inspect subjects, faculty qualifications, student batches, rooms, and institution settings.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    problem = st.session_state.get("problem")

    if problem is None:
        st.warning("⚠️ No dataset is loaded. Please upload a dataset to inspect entities.")
        if st.button("Go to Upload Dataset"):
            st.session_state["nav_selection"] = "Upload Dataset"
            st.rerun()
        return

    st.caption("ℹ️ *Note: Data view is currently read-only. To modify course offerings, teacher loads, or room allocations, update your source CSV and reload.*")

    tabs = st.tabs([
        f"Subjects ({len(problem.subjects)})",
        f"Teachers ({len(problem.teachers)})",
        f"Classes / Groups ({len(problem.student_groups)})",
        f"Rooms ({len(problem.rooms)})",
        "Time Structure & Settings",
    ])

    # 1. Subjects Tab
    with tabs[0]:
        st.subheader("Curriculum Subjects")
        if problem.subjects:
            subj_data = [
                {
                    "Subject ID": s.id,
                    "Name": s.name,
                    "Type": s.subject_type.capitalize(),
                }
                for s in problem.subjects
            ]
            st.dataframe(pd.DataFrame(subj_data), use_container_width=True)
        else:
            st.info("No subjects defined.")

    # 2. Teachers Tab
    with tabs[1]:
        st.subheader("Teaching Faculty")
        if problem.teachers:
            teacher_data = [
                {
                    "Teacher ID": t.id,
                    "Name": t.name,
                    "Qualified Subjects": ", ".join(t.subjects_can_teach) if t.subjects_can_teach else "None",
                    "Max Weekly Load (Slots)": t.maximum_weekly_load,
                    "Unavailable Slots": ", ".join(t.unavailable_slots) if t.unavailable_slots else "None",
                }
                for t in problem.teachers
            ]
            st.dataframe(pd.DataFrame(teacher_data), use_container_width=True)
        else:
            st.info("No teachers defined.")

    # 3. Classes / Groups Tab
    with tabs[2]:
        st.subheader("Student Groups & Course Requirements")
        if problem.student_groups:
            group_summary = []
            detailed_requirements = []

            for g in problem.student_groups:
                total_periods = sum(
                    req.weekly_sessions * req.duration_slots
                    for req in g.subject_requirements
                )
                lunch_str = (
                    ", ".join(f"P{p}" for p in g.lunch_break_periods)
                    if g.lunch_break_periods
                    else "None"
                )
                group_summary.append(
                    {
                        "Class ID": g.id,
                        "Class Name": g.name,
                        "Strength (Students)": g.strength,
                        "Lunch Period(s)": lunch_str,
                        "Required Subjects": len(g.subject_requirements),
                        "Total Weekly Demand (Periods)": total_periods,
                    }
                )

                for req in g.subject_requirements:
                    detailed_requirements.append(
                        {
                            "Class ID": g.id,
                            "Class Name": g.name,
                            "Subject ID": req.subject_id,
                            "Weekly Sessions": req.weekly_sessions,
                            "Duration per Session (Slots)": req.duration_slots,
                            "Total Slots": req.weekly_sessions * req.duration_slots,
                        }
                    )

            st.markdown("##### Batch Summary")
            st.dataframe(pd.DataFrame(group_summary), use_container_width=True)

            st.markdown("##### Detailed Subject Requirements per Batch")
            st.dataframe(pd.DataFrame(detailed_requirements), use_container_width=True)
        else:
            st.info("No student groups defined.")

    # 4. Rooms Tab
    with tabs[3]:
        st.subheader("Rooms & Venues")
        if problem.rooms:
            room_data = [
                {
                    "Room ID": r.id,
                    "Room Name": r.name,
                    "Capacity (Seats)": r.capacity,
                    "Room Type": r.room_type.capitalize(),
                }
                for r in problem.rooms
            ]
            st.dataframe(pd.DataFrame(room_data), use_container_width=True)
        else:
            st.info("No rooms defined.")

    # 5. Time Structure Tab
    with tabs[4]:
        st.subheader("Institution Time Structure")
        ts = problem.time_structure

        c_ts1, c_ts2 = st.columns(2)
        with c_ts1:
            st.markdown(
                f"""
                <div class="academic-card">
                    <h4 style="margin-top:0; color:#1e3a8a;">Daily Operational Settings</h4>
                    <p><strong>Working Days:</strong> {', '.join(ts.working_days)} ({len(ts.working_days)} days)</p>
                    <p><strong>Periods per Day:</strong> {ts.periods_per_day} slots</p>
                    <p><strong>Slot Duration:</strong> {ts.period_duration_minutes} minutes</p>
                    <p><strong>Break Periods:</strong> {', '.join(f'P{p}' for p in ts.break_periods) if ts.break_periods else 'None'}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c_ts2:
            usable_periods_per_day = ts.periods_per_day - len(ts.break_periods)
            total_slots = usable_periods_per_day * len(ts.working_days)
            st.markdown(
                f"""
                <div class="academic-card">
                    <h4 style="margin-top:0; color:#1e3a8a;">Capacity Calculation</h4>
                    <p><strong>Usable Slots/Day:</strong> {usable_periods_per_day} slots (excluding breaks)</p>
                    <p><strong>Total Weekly Teaching Slots:</strong> {total_slots} slots per class</p>
                    <p><strong>Total Room Periods Available:</strong> {total_slots * len(problem.rooms)} slot-rooms</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
