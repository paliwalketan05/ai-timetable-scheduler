"""Experiments & Metrics view for comparing algorithm performance across datasets."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def render_experiments_page():
    st.markdown(
        """
        <div class="page-header">
            <h1 class="page-title">Algorithm Experiments & Metrics</h1>
            <p class="page-subtitle">Empirical performance benchmarking across Plain Backtracking, Heuristic Backtracking, and Min-Conflicts.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    history = st.session_state.get("experiments_history", [])

    # Check if any experiment runs exist in session or benchmark results
    if not history:
        st.info(
            "📊 **No experimental runs have been executed yet.**\n\n"
            "Benchmark comparisons will appear here after executing solver runs or running the benchmark suite "
            "(`experiments/benchmark.py`). In accordance with project integrity standards, no fabricated experimental data is displayed.",
            icon="ℹ️",
        )

        st.markdown("### Planned Benchmark Methodology")
        st.markdown(
            """
            As defined in the project architecture (`docs/architecture.md`), the comparative experiment protocol requires:
            - **Controlled Datasets:** Small dataset (`data/small/`) and Large multi-department dataset (`data/large/`).
            - **10 Trials per Randomized Solver:** Repeated runs for stochastic solvers (Min-Conflicts, Simulated Annealing) to calculate mean runtime, standard deviation, and success rates.
            - **Fair Comparison:** Consistent time limits (e.g. 60 seconds), common penalty functions, and independent validation.
            """
        )

        # Expected Schema Table Preview
        preview_schema = pd.DataFrame([
            {
                "Algorithm": "Baseline Backtracking",
                "Dataset": "small",
                "Runtime (s)": "Pending",
                "Nodes / Iterations": "Pending",
                "Hard Violations": "Pending",
                "Soft Penalty": "Pending",
                "Success Rate": "Pending",
                "Seed": "N/A",
            },
            {
                "Algorithm": "Heuristic Backtracking (MRV+Degree+FC)",
                "Dataset": "small",
                "Runtime (s)": "Pending",
                "Nodes / Iterations": "Pending",
                "Hard Violations": "Pending",
                "Soft Penalty": "Pending",
                "Success Rate": "Pending",
                "Seed": "N/A",
            },
            {
                "Algorithm": "Min-Conflicts Local Search",
                "Dataset": "small",
                "Runtime (s)": "Pending",
                "Nodes / Iterations": "Pending",
                "Hard Violations": "Pending",
                "Soft Penalty": "Pending",
                "Success Rate": "Pending",
                "Seed": "42 (Run 1/10)",
            },
        ])
        st.markdown("##### Benchmark Schema Preview")
        st.dataframe(preview_schema, use_container_width=True)
        return

    # If history contains actual runs, render real charts and tables
    st.subheader("Historical Solver Trials")
    df_history = pd.DataFrame(history)
    st.dataframe(df_history, use_container_width=True)

    # Visualizations using Plotly
    c_ch1, c_ch2 = st.columns(2)

    with c_ch1:
        if "algorithm" in df_history.columns and "runtime_seconds" in df_history.columns:
            fig_runtime = px.bar(
                df_history,
                x="algorithm",
                y="runtime_seconds",
                color="status",
                title="Runtime Comparison by Algorithm",
                labels={"runtime_seconds": "Runtime (seconds)", "algorithm": "Algorithm"},
                color_discrete_map={"Success": "#10b981", "No Solution Found": "#ef4444"},
            )
            fig_runtime.update_layout(template="plotly_white")
            st.plotly_chart(fig_runtime, use_container_width=True)

    with c_ch2:
        if "hard_violations" in df_history.columns and "soft_penalty" in df_history.columns:
            fig_violations = px.scatter(
                df_history,
                x="hard_violations",
                y="soft_penalty",
                color="algorithm",
                size="runtime_seconds" if "runtime_seconds" in df_history.columns else None,
                title="Hard Violations vs Soft Penalty",
                labels={"hard_violations": "Hard Violations", "soft_penalty": "Soft Penalty"},
            )
            fig_violations.update_layout(template="plotly_white")
            st.plotly_chart(fig_violations, use_container_width=True)

    if st.button("Clear Experiment History"):
        st.session_state["experiments_history"] = []
        st.rerun()
