"""Generate Timetable view for algorithm selection, solver configuration, and CSP domain analysis."""

import importlib
import time
import streamlit as st
import pandas as pd

from src.csp.sessions import expand_sessions
from src.csp.domains import generate_domains
from src.ui.state import set_timetable_result
from src.ui.styles import render_badge


ALGORITHMS = {
    "backtracking": {
        "name": "Baseline Backtracking CSP",
        "module": "src.solvers.backtracking",
        "description": "Exhaustive depth-first search assigning variables recursively with chronologic backtracking.",
    },
    "heuristic_backtracking": {
        "name": "Improved Heuristic Backtracking (MRV + Degree + FC)",
        "module": "src.solvers.heuristics",
        "description": "Backtracking enhanced by Minimum Remaining Values (MRV), Degree Heuristic, and Forward Checking.",
    },
    "min_conflicts": {
        "name": "Min-Conflicts Local Search",
        "module": "src.solvers.min_conflicts",
        "description": "Iterative repair algorithm choosing conflicted variables and assigning values that minimize violations.",
    },
    "simulated_annealing": {
        "name": "Simulated Annealing (Optional)",
        "module": "src.solvers.simulated_annealing",
        "description": "Stochastic metaheuristic exploring state space with temperature-dependent acceptance of worsening moves.",
    },
    "hybrid": {
        "name": "Hybrid Backtracking + SA (Optional)",
        "module": "src.solvers.hybrid",
        "description": "Two-phase solver: constructive backtracking followed by simulated annealing soft-constraint optimization.",
    },
}


def check_algorithm_implementation(module_name: str) -> bool:
    """Inspect whether a solver module contains an active solve() callable."""
    try:
        mod = importlib.import_module(module_name)
        # Check if mod has a callable named 'solve' or 'run_solver' or similar
        for attr in ["solve", "run_solver", "solve_timetable"]:
            if hasattr(mod, attr) and callable(getattr(mod, attr)):
                return True
        return False
    except Exception:
        return False


def render_generate_page():
    st.markdown(
        """
        <div class="page-header">
            <h1 class="page-title">Generate Academic Timetable</h1>
            <p class="page-subtitle">Configure search parameters, analyze CSP variable domains, and execute scheduling algorithms.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    problem = st.session_state.get("problem")
    val_errors = st.session_state.get("validation_errors", [])

    if problem is None:
        st.warning("⚠️ No dataset is currently loaded. Please load a dataset first.")
        if st.button("📁 Go to Upload Dataset"):
            st.session_state["nav_selection"] = "Upload Dataset"
            st.rerun()
        return

    if val_errors:
        st.error(
            f"❌ The active dataset contains **{len(val_errors)} validation errors**. "
            "Resolve these issues in your CSV data before generating timetables."
        )
        for err in val_errors:
            st.write(f"- {err}")
        return

    # Check solver module implementations dynamically
    algorithm_statuses = {}
    for key, info in ALGORITHMS.items():
        is_implemented = check_algorithm_implementation(info["module"])
        algorithm_statuses[key] = is_implemented

    # 1. Algorithm Selection
    st.subheader("1. Solver Selection")

    algo_options = list(ALGORITHMS.keys())
    algo_labels = [
        f"{ALGORITHMS[k]['name']} {'[Ready]' if algorithm_statuses[k] else '[Pending Implementation]'}"
        for k in algo_options
    ]

    selected_index = st.selectbox(
        "Choose Scheduling Algorithm",
        range(len(algo_options)),
        format_func=lambda idx: algo_labels[idx],
    )
    selected_key = algo_options[selected_index]
    selected_info = ALGORITHMS[selected_key]
    is_available = algorithm_statuses[selected_key]

    st.markdown(f"*{selected_info['description']}*")

    if not is_available:
        st.markdown(
            f"""
            <div style="background-color:#fffbeb; border:1px solid #fde68a; border-radius:8px; padding:12px 16px; color:#92400e; font-size:0.9rem; margin-top:10px;">
                ⚠️ <strong>Solver Module Status:</strong> The solver logic in <code>{selected_info['module']}</code> is currently an incomplete placeholder.
                In accordance with project guidelines, the UI does not simulate fake search results. You can inspect the CSP session expansion and domain feasibility below while backend solver development is completed.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 2. Solver Parameters (Disabled if not implemented)
    st.subheader("2. Search Parameters & Heuristics")
    c_p1, c_p2, c_p3 = st.columns(3)
    with c_p1:
        time_limit = st.slider("Time Limit (seconds)", min_value=1, max_value=60, value=10, disabled=not is_available)
    with c_p2:
        max_iterations = st.number_input("Max Search Nodes / Iterations", min_value=100, max_value=100000, value=5000, step=500, disabled=not is_available)
    with c_p3:
        random_seed = st.number_input("Random Seed (for stochastic solvers)", min_value=0, max_value=999999, value=42, disabled=not is_available)

    # 3. CSP Problem Formulation Inspection (Variables & Domains)
    st.subheader("3. CSP Formulation Analysis")
    st.markdown("Before running search, the system expands weekly course requirements into scheduling variables and filters valid assignment domains:")

    try:
        sessions = expand_sessions(problem)
        domains = generate_domains(problem, sessions)

        total_sessions = len(sessions)
        empty_domains = [s.id for s in sessions if len(domains.get(s.id, [])) == 0]
        avg_domain_size = (
            sum(len(d) for d in domains.values()) / total_sessions
            if total_sessions > 0
            else 0
        )

        d1, d2, d3, d4 = st.columns(4)
        with d1:
            st.metric("Total Variables (Sessions)", total_sessions)
        with d2:
            st.metric("Avg Domain Size", f"{avg_domain_size:.1f} slots")
        with d3:
            st.metric("Empty Domains", len(empty_domains))
        with d4:
            st.metric("CSP Status", "Feasible Initial Domains" if not empty_domains else "Infeasible")

        if empty_domains:
            st.error(
                f"🚨 **Infeasibility Detected:** {len(empty_domains)} session(s) have 0 valid candidate placements! "
                f"Sessions: {', '.join(empty_domains[:5])}. Check teacher qualifications, room capacities, or availability."
            )

        with st.expander("🔍 Inspect Variables and Candidate Domains"):
            domain_table = [
                {
                    "Session ID": s.id,
                    "Class": s.group_id,
                    "Subject": s.subject_id,
                    "Duration (Slots)": s.duration_slots,
                    "Domain Size (|D|)": len(domains.get(s.id, [])),
                    "Eligible Sample": ", ".join(
                        f"{a.day}_{a.start_period}({a.teacher_id},{a.room_id})"
                        for a in domains.get(s.id, [])[:3]
                    )
                    + ("..." if len(domains.get(s.id, [])) > 3 else ""),
                }
                for s in sessions
            ]
            st.dataframe(pd.DataFrame(domain_table), use_container_width=True)

    except Exception as exc:
        st.error(f"Error computing CSP sessions/domains: {exc}")
        sessions = []
        domains = {}

    # 4. Generate Button
    st.subheader("4. Execute Timetable Generation")

    btn_label = f"🚀 Run {selected_info['name']}" if is_available else "🔒 Solver Implementation Pending"
    
    if st.button(btn_label, type="primary", disabled=not is_available, use_container_width=True):
        if is_available:
            with st.spinner(f"Executing {selected_info['name']}..."):
                start_time = time.perf_counter()
                try:
                    mod = importlib.import_module(selected_info["module"])
                    solver_func = getattr(mod, "solve", None) or getattr(mod, "solve_timetable", None)
                    
                    timetable, metrics = solver_func(
                        problem,
                        time_limit=time_limit,
                        max_iterations=max_iterations,
                        seed=random_seed,
                    )
                    elapsed = time.perf_counter() - start_time

                    metrics_dict = {
                        "algorithm": selected_info["name"],
                        "status": "Success" if timetable is not None else "No Solution Found",
                        "runtime_seconds": elapsed,
                        "scheduled_count": len(timetable.sessions) if timetable else 0,
                        "unscheduled_count": len(sessions) - (len(timetable.sessions) if timetable else 0),
                        "hard_violations": metrics.get("hard_violations", 0) if isinstance(metrics, dict) else 0,
                        "soft_penalty": metrics.get("soft_penalty", 0) if isinstance(metrics, dict) else 0,
                        "nodes_expanded": metrics.get("nodes_expanded", 0) if isinstance(metrics, dict) else 0,
                    }

                    set_timetable_result(timetable, metrics_dict)
                    st.success(f"Timetable generated in {elapsed:.3f} seconds!")
                    st.rerun()

                except Exception as exc:
                    st.error(f"Solver encountered an error during execution: {exc}")
