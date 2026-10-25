# Project Requirements

## 1. Problem Statement
Develop an AI-based timetable scheduler that automatically assigns lectures and laboratory sessions to teachers, classes, rooms, and time slots without violating hard constraints. Compare search algorithms using common datasets and evaluation metrics.

## 2. Functional Requirements
- **FR-01:** Accept input through forms, CSV, or JSON.
- **FR-02:** Validate input data and references.
- **FR-03:** Generate timetables using the selected algorithm.
- **FR-04:** Enforce hard constraints and evaluate soft constraints.
- **FR-05:** Independently validate every generated timetable.
- **FR-06:** Support Backtracking, Heuristic Backtracking, and Min-Conflicts.
- **FR-07:** Display timetables by class, teacher, and room.
- **FR-08:** Report runtime, search effort, violations, and soft penalty.
- **FR-09:** Export timetables to CSV or Excel.
- **FR-10:** Allow manual edits with immediate conflict checking.
- **FR-11:** Report infeasibility, timeouts, and failed searches clearly.

## 3. Input Data
- **Subjects:** code, name, weekly hours, type (theory/lab).
- **Teachers:** name, qualified subjects, unavailable slots, maximum weekly load.
- **Classes/Batches:** name, student strength, subjects, lunch-break slot.
- **Rooms:** name, capacity, type (classroom/lab).
- **Time structure:** working days, periods per day, break periods.

## 4. Hard Constraints
- **H1:** A teacher cannot teach two sessions simultaneously.
- **H2:** A class cannot attend two sessions simultaneously.
- **H3:** A room cannot host two sessions simultaneously.
- **H4:** Room capacity must accommodate the class.
- **H5:** Lab sessions must use lab rooms; theory sessions must use classrooms.
- **H6:** Teachers must not be scheduled during unavailable slots.
- **H7:** Each subject must receive exactly its required weekly hours.
- **H8:** Teacher workload must not exceed the maximum weekly load.
- **H9:** No class may have a session during its assigned lunch break.

## 5. Soft Constraints
Implement at least three:
- **S1:** Minimize gaps and free periods in a class timetable.
- **S2:** Spread subject sessions across different days.
- **S3:** Schedule laboratory sessions in consecutive periods.
- **S4:** Respect teacher preferences, such as avoiding first-period classes.
- **S5:** Avoid more than two consecutive lectures for a teacher.

## 6. Problem Formulation
Each variable represents an individual required teaching session. Its domain contains feasible day, period, and room combinations. Teacher assignment may be fixed using a subject-teacher mapping.

Hard constraints restrict feasible assignments. Soft constraints determine timetable quality.

Recommended cost function:

`Cost = 1000 × hard violations + soft penalties`

A timetable is valid only when its hard-constraint violation count is zero.

## 7. Algorithms
1. Plain Backtracking as the baseline.
2. Heuristic Backtracking with at least three improvements, preferably MRV, Forward Checking, and Degree Heuristic.
3. Min-Conflicts with an initial assignment strategy, conflicted-variable selection, tie-breaking, iteration limit, and plateau escape.

Optional bonus algorithms are Simulated Annealing and Hybrid Backtracking + SA.

The `python-constraint` package may be used as a cross-check but not as the main solver.

## 8. Acceptance Criteria
- Both required datasets can be loaded and validated.
- Solvers return results in a common format.
- Every result is independently checked.
- Valid timetables have zero hard violations.
- Timetables can be viewed and exported.
- Experiments record reproducible metrics.
- Errors and infeasible problems are reported clearly.