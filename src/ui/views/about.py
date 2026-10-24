"""About Project view presenting the problem statement, CSP formulation, and implementation roadmap."""

import streamlit as st


def render_about_page():
    st.markdown(
        """
        <div class="page-header">
            <h1 class="page-title">About the Project</h1>
            <p class="page-subtitle">AI-Based Timetable Scheduler &bull; 2nd Year B.Tech Academic Project</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="academic-card" style="border-left: 4px solid #1e3a8a;">
            <p style="font-size: 1.05rem; line-height: 1.6; color: #1e293b; margin: 0;">
                <strong>Project Mission:</strong> An AI-based academic timetable scheduler that models timetable generation
                as a <strong>Constraint Satisfaction Problem (CSP)</strong> and compares search and optimization algorithms
                while enforcing hard constraints and evaluating soft constraints.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_a1, col_a2 = st.columns(2)

    with col_a1:
        st.subheader("Implementation Status")
        st.markdown(
            """
            | System Component | Implementation Status | Notes |
            |---|---|---|
            | **Entities & Schedule Models** | ✅ Completed | `src/models/` dataclasses |
            | **CSV Ingestion & Preprocessing** | ✅ Completed | `src/data/loaders.py` |
            | **Input Consistency Validation** | ✅ Completed | `src/data/validation.py` |
            | **CSP Session Expansion** | ✅ Completed | `src/csp/sessions.py` |
            | **Domain Generation Engine** | ✅ Completed | `src/csp/domains.py` |
            | **Streamlit UI & Multi-view Grid** | ✅ Completed | `app.py`, `src/ui/` |
            | **Baseline Backtracking CSP** | 🚧 Planned / Underway | `src/solvers/backtracking.py` |
            | **Heuristic Backtracking (MRV+Deg+FC)** | 🚧 Planned / Underway | `src/solvers/heuristics.py` |
            | **Min-Conflicts Local Search** | 🚧 Planned / Underway | `src/solvers/min_conflicts.py` |
            | **Simulated Annealing & Hybrid** | 🚧 Optional / Roadmap | `src/solvers/simulated_annealing.py` |
            | **Independent Constraint Validator** | 🚧 Planned / Underway | `src/evaluation/validator.py` |
            | **Benchmarking Suite** | 🚧 Planned / Underway | `experiments/benchmark.py` |
            """
        )

    with col_a2:
        st.subheader("Mathematical CSP Formulation")
        st.markdown(
            r"""
            - **Variables ($X_i$):** Each individual teaching session required by a student group for a subject.
            - **Domains ($D_i$):** All valid tuples $(t, d, p, r)$ where:
              - $t$: Qualified instructor for the subject ($s \in t.\text{subjects}$).
              - $d, p$: Feasible day and starting period fitting within daily bounds, not conflicting with institutional breaks or class lunch breaks.
              - $r$: Room with capacity $\ge$ class strength and matching room type (lab for lab subjects, classroom for theory).
            - **Objective Cost Function:**
              $$\text{Cost} = 1000 \times H + S$$
              Where $H$ is the total hard constraint violation count (strictly 0 for validity), and $S$ is the soft constraint penalty.
            """
        )

    st.markdown("---")
    st.subheader("Technology Stack & Architecture Principles")
    t1, t2, t3, t4 = st.columns(4)
    with t1:
        st.markdown("**Core Language**\n\nPython 3.14 / 3.11+\nDataclasses, Type Hints")
    with t2:
        st.markdown("**User Interface**\n\nStreamlit\nInteractive web dashboard")
    with t3:
        st.markdown("**Data Handling**\n\nPandas & openpyxl\nCSV & Excel processing")
    with t4:
        st.markdown("**Verification**\n\nPytest & Metrics\nAutomated test suite")
