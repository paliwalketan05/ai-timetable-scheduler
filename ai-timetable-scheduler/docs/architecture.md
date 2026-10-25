# AI Timetable Generator — System Architecture

## 1. Project Overview

### Purpose
A Python-based application that generates academic timetables using constraint-satisfaction and optimization algorithms.

### Objectives
- Generate timetables satisfying all hard constraints.
- Improve timetable quality by optimizing soft constraints.
- Implement and compare five solver configurations.
- Independently validate generated timetables.
- Evaluate solver performance using consistent metrics.
- Provide an interactive interface for generating and viewing timetables.

### Design Principles
- **Modularity:** Separate the interface, scheduling logic, solvers, and validation.
- **Reusability:** Use a common data model across all solvers.
- **Correctness:** Independently verify generated timetables.
- **Comparability:** Evaluate solvers using consistent datasets and metrics.

---

## 2. System Architecture

### 2.1 Architecture Diagram

flowchart TD
    U[User] --> UI[Streamlit Interface]
    UI --> IV[Input Validation]
    IV --> CP[Problem Preparation]
    CP --> S[Solver Engine]
    C[Constraint Logic] -.-> S

    S --> V[Independent Validator]
    V --> E[Evaluation Module]
    E --> R[Results and Timetable Display]
    R --> UI

### 2.2 Component Responsibilities

| Component | Responsibility |
|---|---|
| Streamlit Interface | Collect input and display results. |
| Input Validation | Check input completeness, types, and basic consistency. |
| Problem Preparation | Convert input into a standardized scheduling representation. |
| Constraint Logic | Define hard constraints and soft-constraint scoring. |
| Solver Engine | Generate or optimize timetables using the selected algorithm. |
| Independent Validator | Verify completed timetables against hard constraints. |
| Evaluation Module | Measure runtime, success rate, and timetable quality. |

The constraint logic is used during solver execution. The independent validator checks the completed result separately.

---

## 3. System Workflow

1. **Input:** Collect courses, faculty, rooms, student groups, time slots, and scheduling requirements.
2. **Input Validation:** Reject malformed or inconsistent input.
3. **Problem Preparation:** Build the common scheduling problem representation.
4. **Solver Execution:** Run the selected algorithm using the shared constraint logic.
5. **Independent Validation:** Check the returned timetable against every hard constraint.
6. **Evaluation:** Calculate performance metrics and soft-constraint scores.
7. **Output:** Display the timetable, validation status, and evaluation results.

**Failure handling:** Report invalid input, unsolvable problems, or unsuccessful solver runs clearly. Never present an invalid timetable as a valid solution.

---

## 4. Project Directory Structure

ai-timetable-scheduler/
├── app.py
├── src/
│   ├── models/
│   │   ├── entities.py
│   │   └── schedule.py
│   ├── data/
│   │   ├── loaders.py
│   │   └── validation.py
│   ├── csp/
│   │   ├── variables.py
│   │   ├── domains.py
│   │   └── constraints.py
│   ├── solvers/
│   │   ├── backtracking.py
│   │   ├── heuristics.py
│   │   ├── min_conflicts.py
│   │   ├── simulated_annealing.py
│   │   └── hybrid.py
│   ├── evaluation/
│   │   ├── validator.py
│   │   └── metrics.py
│   └── services/
│       └── scheduler.py
├── data/
│   ├── small/
│   └── large/
├── experiments/
│   ├── benchmark.py
│   └── results/
├── tests/
├── docs/
│   ├── requirements.md
│   ├── architecture.md
│   ├── data-model.md
│   └── wireframes.md
├── requirements.txt
└── README.md

*This is the planned structure; files will be created as implementation progresses.*

### Module Responsibilities

- `models/`: Represent courses, faculty, rooms, time slots, and schedules.
- `data/`: Load input data and validate its structure.
- `csp/`: Define variables, domains, and scheduling constraints.
- `solvers/`: Implement the five solver configurations independently.
- `evaluation/`: Validate results and calculate evaluation metrics.
- `services/`: Coordinate scheduling, solver execution, and result handling.
- `experiments/`: Run benchmarks and store experimental results.
- `tests/`: Verify correctness, constraints, and solver behavior.
- `app.py`: Provide the Streamlit user interface.

---

## 5. Solver Architecture

All solvers will use a common data model and compatible input/output interfaces. Their internal algorithms will remain independent of the user interface.

| ID | Solver configuration | Main approach |
|---|---|---|
| S1 | Backtracking | Assign variables recursively and backtrack when assignments violate constraints. |
| S2 | Heuristic Backtracking | Use Minimum Remaining Values (MRV), Degree heuristic, and Forward Checking to improve search. |
| S3 | Min-Conflicts | Iteratively change assignments to reduce conflicts. |
| S4 | Simulated Annealing | Explore candidate schedules using probabilistic acceptance of changes. |
| S5 | Hybrid Backtracking + Simulated Annealing | Construct a schedule using backtracking, then attempt to improve it using simulated annealing. |

### Common Solver Contract

Each solver receives a prepared scheduling problem and its configuration. It returns a result containing the candidate timetable, execution status, runtime, and relevant statistics.

The common interface allows the evaluation module to compare different algorithms consistently.

---

## 6. Data, Constraints, and Validation

### 6.1 Data Model

The system will represent:

- **Courses:** Course identity, required teaching hours, and session requirements.
- **Faculty:** Teaching assignments and availability.
- **Rooms:** Room availability and relevant capacity or suitability information.
- **Student Groups:** Groups that attend scheduled sessions.
- **Time Slots:** Available days and periods.
- **Assignments:** The course, faculty, group, room, and time slot associated with a scheduled session.
- **Timetable:** A collection of assignments representing a complete or candidate schedule.

### 6.2 Constraint Handling

The system will implement the nine agreed hard constraints and five agreed soft constraints, as defined in `requirements.md`.

- **Hard constraints:** Mandatory rules that every valid timetable must satisfy.
- **Soft constraints:** Preferences used to evaluate and improve timetable quality.

Constraint logic will be shared wherever possible to maintain consistent scheduling rules across solvers.

### 6.3 Independent Validation

The validator will examine the completed timetable independently of the solver's internal search state.

It will check all hard constraints, report violations, and determine whether the result can be accepted as valid. Shared rule definitions may be reused, but final validation must not simply trust the solver's internal checks.

---

## 7. Technology Stack and Design Decisions

| Technology | Purpose |
|---|---|
| Python | Core implementation and solver algorithms. |
| Streamlit | Interactive user interface. |
| pandas | Structured data processing and experiment results. |
| pytest | Automated testing. |
| python-constraint | Independent cross-checks on suitable small scheduling problems, not the primary solver engine. |
| Mermaid | Architecture diagrams in Markdown documentation. |

### Key Design Decisions

- Keep solver implementations independent of Streamlit.
- Use a common data model and solver interface.
- Separate input validation from final timetable validation.
- Keep hard constraints separate conceptually from soft-constraint scoring.
- Use consistent datasets, configurations, and metrics for solver comparisons.
- Avoid introducing a database or separate backend service unless future requirements justify them.

---

## 8. Evaluation and Experiments

The five solver configurations will be evaluated on common test datasets under controlled conditions.

### Evaluation Metrics

- **Runtime:** Time required to produce a result.
- **Success rate:** Proportion of runs that produce a valid timetable.
- **Hard-constraint violations:** Number of mandatory rules violated in a candidate result.
- **Soft-constraint score:** Measure of how well a timetable satisfies scheduling preferences.
- **Search statistics:** Relevant measures such as explored nodes, iterations, or backtracks where applicable.

### Fair Comparison

- Use the same scheduling inputs for comparable runs.
- Record solver configurations and random seeds where applicable.
- Perform repeated runs for randomized algorithms; the planned benchmark uses ten runs per configuration and dataset.
- Record unsuccessful runs rather than excluding them from the results.
- Report runtime and solution quality together instead of judging solvers by speed alone.

### Objective Function

For optimization experiments, the agreed cost function is:

`Cost = 1000 × H + S`

Where:

- `H` is the hard-constraint violation count.
- `S` is the soft-constraint penalty.

The large penalty for hard violations discourages invalid schedules. However, the independent validator remains the final authority on whether a timetable is valid.

---

## 9. Error Handling, Testing, and Future Extensions

### Error Handling
- Reject malformed or inconsistent input with actionable messages.
- Handle solver timeouts, search failures, and unsolvable scheduling problems.
- Distinguish between no solution found and a proven absence of a solution.
- Prevent invalid schedules from being presented as valid.

### Testing Strategy
- **Unit tests:** Test individual models, constraints, solvers, and metrics.
- **Integration tests:** Verify data flow between the application components.
- **Validation tests:** Test known-valid and known-invalid timetables.
- **Benchmark tests:** Compare solver performance on common datasets.
- **Regression tests:** Ensure future changes do not break existing behavior.

### Possible Future Extensions
- Manual timetable editing with revalidation.
- Timetable export to common formats.
- Larger datasets and additional optimization strategies.
- Improved visualization and reporting.

These extensions are not part of the initial implementation unless explicitly added to the project requirements.

---

## Architecture Status

This document describes the planned system architecture. Individual modules, interfaces, and implementation details will be verified and refined as development progresses. Changes to core design decisions should be reflected in this document.