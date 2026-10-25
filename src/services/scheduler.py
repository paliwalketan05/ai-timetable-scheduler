"""Coordinate input validation, solver selection, and timetable evaluation."""

from dataclasses import asdict

from src.data.validation import validate_timetable_input
from src.evaluation.metrics import calculate_soft_penalty
from src.evaluation.validator import validate_timetable

from src.solvers.backtracking import solve_with_stats as backtracking
from src.solvers.heuristic_backtracking import solve_with_stats as heuristic
from src.solvers.min_conflicts import solve_with_stats as min_conflicts
from src.solvers.simulated_annealing import solve_with_stats as annealing
from src.solvers.hybrid import solve_with_stats as hybrid


ALGORITHMS = {
    "Backtracking": backtracking,
    "Heuristic Backtracking": heuristic,
    "Min-Conflicts": min_conflicts,
    "Simulated Annealing": annealing,
    "Hybrid": hybrid,
}


def run_scheduler(problem, algorithm="Heuristic Backtracking",
                  max_steps=2000, seed=42):
    """Validate input, run a solver, and independently validate its result."""

    input_errors = validate_timetable_input(problem)
    if input_errors:
        raise ValueError(
            "Input validation failed:\n" + "\n".join(input_errors)
        )

    if algorithm not in ALGORITHMS:
        raise ValueError(f"Unknown algorithm: {algorithm}")

    solver = ALGORITHMS[algorithm]

    if algorithm == "Min-Conflicts":
        result = solver(
            problem, max_steps=max_steps, seed=seed
        )
    elif algorithm == "Simulated Annealing":
        result = solver(
            problem, max_steps=max_steps, seed=seed
        )
    elif algorithm == "Hybrid":
        result = solver(
            problem, max_steps=max_steps, seed=seed
        )
    else:
        result = solver(problem)

    timetable = result.timetable
    stats = asdict(result.stats)

    if timetable is None:
        return {
            "success": False,
            "timetable": None,
            "violations": [],
            "stats": stats,
            "penalties": None,
            "message": "No valid timetable could be generated.",
        }

    violations = validate_timetable(timetable, problem)

    if violations:
        return {
            "success": False,
            "timetable": timetable,
            "violations": violations,
            "stats": stats,
            "penalties": None,
            "message": "The generated timetable failed validation.",
        }

    penalties = calculate_soft_penalty(timetable)

    return {
        "success": True,
        "timetable": timetable,
        "violations": [],
        "stats": stats,
        "penalties": penalties,
        "message": "A valid timetable was generated.",
    }
