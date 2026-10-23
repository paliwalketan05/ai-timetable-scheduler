
"""Run assignment-required solver comparisons on both CSV datasets."""

import csv
import random
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.data.loaders import load_timetable_csv
from src.data.validation import validate_timetable_input
from src.evaluation.metrics import calculate_soft_penalty
from src.evaluation.validator import validate_timetable
from src.models.schedule import Timetable
from src.solvers.backtracking import solve_with_stats as basic_backtracking
from src.solvers.heuristic_backtracking import solve_with_stats as heuristic_solve
from src.solvers.min_conflicts import solve_with_stats as min_conflicts_solve
from src.solvers.simulated_annealing import solve_with_stats as annealing_solve
from src.solvers.hybrid import solve_with_stats as hybrid_solve

ROOT = Path(__file__).resolve().parents[1]
DATASETS = [
    ROOT / "experiments/datasets/assignment_small.csv",
    ROOT / "experiments/datasets/assignment_large.csv",
]
OUTPUT = ROOT / "experiments/results"
RANDOMIZED_SOLVERS = {"min_conflicts", "simulated_annealing", "hybrid"}
REPETITIONS = 10


def run_one(solver_name, problem, seed):
    """Run one solver and return a timetable, statistics and elapsed time."""
    stats = {}
    start = time.perf_counter()
    cost_history=[]

    if solver_name == "basic_backtracking":
        result = basic_backtracking(problem)
        timetable = result.timetable
        stats = {
            "nodes_explored": result.stats.nodes_explored,
            "backtracks": result.stats.backtracks,
        }

    elif solver_name == "heuristic_backtracking":
        result = heuristic_solve(problem)
        timetable = result.timetable
        stats = {
            "nodes_explored": result.stats.nodes_explored,
            "backtracks": result.stats.backtracks,
        }

    elif solver_name == "min_conflicts":
        result = min_conflicts_solve(problem, seed=seed)
        timetable = result.timetable
        cost_history = result.stats.cost_history
        stats = {
            "iterations": result.stats.iterations,
            "restarts": result.stats.restarts,
            "plateau_escapes": result.stats.plateau_escapes,
        }

    elif solver_name == "simulated_annealing":
        result = annealing_solve(problem, seed=seed)
        timetable = result.timetable
        stats = {
            "iterations": result.stats.iterations,
            "accepted_moves": result.stats.accepted_moves,
            "worse_moves_accepted": result.stats.worse_moves_accepted,
            "restarts": result.stats.restarts,
        }

    elif solver_name == "hybrid":
        result = hybrid_solve(problem, seed=seed)
        timetable = result.timetable
        stats = {
            "backtracking_nodes": result.stats.backtracking_nodes,
            "backtracking_backtracks": result.stats.backtracking_backtracks,
            "annealing_iterations": result.stats.annealing_iterations,
            "annealing_accepted_moves": result.stats.annealing_accepted_moves,
        }

    else:
        raise ValueError(f"Unknown solver: {solver_name}")

    elapsed = time.perf_counter() - start

    violations = (
        validate_timetable(timetable, problem)
        if timetable is not None
        else ["Solver did not find a timetable."]
    )

    penalties = (
        calculate_soft_penalty(timetable)
        if timetable is not None and not violations
        else None
    )

    return {
        "timetable": timetable,
        "runtime_seconds": elapsed,
        "success": timetable is not None and not violations,
        "hard_violations": len(violations),
        "violation_details": violations,
        "soft_penalties": penalties,
        "statistics": stats,
        "cost_history": cost_history,
    }


def write_csv(path, rows):
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    detail_rows = []
    summary_rows = []
    history_rows = []

    solver_names = [
        "basic_backtracking",
        "heuristic_backtracking",
        "min_conflicts",
        "simulated_annealing",
        "hybrid",
    ]

    for dataset_path in DATASETS:
        problem = load_timetable_csv(dataset_path)
        input_errors = validate_timetable_input(problem)
        if input_errors:
            raise ValueError(f"{dataset_path.name}: {input_errors}")

        dataset_name = dataset_path.stem
        print(f"\n{'=' * 76}\nDATASET: {dataset_name}\n{'=' * 76}")

        for solver_name in solver_names:
            repetitions = REPETITIONS if solver_name in RANDOMIZED_SOLVERS else 1
            outcomes = []

            for repetition in range(repetitions):
                seed = 42 + repetition
                outcome = run_one(solver_name, problem, seed)
                outcomes.append(outcome)

                # Save the actual first Min-Conflicts benchmark run.
                if solver_name == "min_conflicts" and repetition == 0:
                    for point in outcome["cost_history"]:
                        history_rows.append({
                            "dataset": dataset_name,
                            **point,
                        })

                stats = outcome["statistics"]
                detail_rows.append({
                    "dataset": dataset_name,
                    "solver": solver_name,
                    "run": repetition + 1,
                    "seed": seed if solver_name in RANDOMIZED_SOLVERS else "",
                    "success": outcome["success"],
                    "runtime_seconds": round(outcome["runtime_seconds"], 6),
                    "hard_violations": outcome["hard_violations"],
                    "soft_penalty_total": (
                        outcome["soft_penalties"]["total"]
                        if outcome["soft_penalties"] is not None else ""
                    ),
                    "soft_class_gaps": (
                        outcome["soft_penalties"]["class_gaps"]
                        if outcome["soft_penalties"] is not None else ""
                    ),
                    "soft_subject_distribution": (
                        outcome["soft_penalties"]["subject_distribution"]
                        if outcome["soft_penalties"] is not None else ""
                    ),
                    "soft_teacher_consecutive": (
                        outcome["soft_penalties"]["teacher_consecutive"]
                        if outcome["soft_penalties"] is not None else ""
                    ),
                    "nodes_explored": stats.get("nodes_explored", ""),
                    "backtracks": stats.get("backtracks", ""),
                    "iterations": stats.get("iterations", ""),
                    "restarts": stats.get("restarts", ""),
                    "plateau_escapes": stats.get("plateau_escapes", ""),
                    "backtracking_nodes": stats.get("backtracking_nodes", ""),
                    "annealing_iterations": stats.get("annealing_iterations", ""),
                })

            successful = [item for item in outcomes if item["success"]]
            valid_penalties = [
                item["soft_penalties"]["total"]
                for item in successful
                if item["soft_penalties"] is not None
            ]

            summary = {
                "dataset": dataset_name,
                "solver": solver_name,
                "runs": repetitions,
                "successful_runs": len(successful),
                "success_rate_percent": round(
                    100 * len(successful) / repetitions, 1
                ),
                "average_runtime_seconds": round(
                    sum(item["runtime_seconds"] for item in outcomes)
                    / repetitions,
                    6,
                ),
                "average_hard_violations": round(
                    sum(item["hard_violations"] for item in outcomes)
                    / repetitions,
                    3,
                ),
                "average_soft_penalty_valid_runs": (
                    round(sum(valid_penalties) / len(valid_penalties), 3)
                    if valid_penalties else ""
                ),
                "best_soft_penalty": min(valid_penalties) if valid_penalties else "",
            }
            summary_rows.append(summary)

            print(
                f"{solver_name:24} "
                f"success={summary['success_rate_percent']:5.1f}% "
                f"time={summary['average_runtime_seconds']:.6f}s "
                f"hard={summary['average_hard_violations']} "
                f"soft={summary['average_soft_penalty_valid_runs']}"
            )

    write_csv(OUTPUT / "solver_runs.csv", detail_rows)
    write_csv(OUTPUT / "solver_summary.csv", summary_rows)
    write_csv(OUTPUT / "min_conflicts_cost_history.csv", history_rows)

    if history_rows:
        for dataset_name in sorted({row["dataset"] for row in history_rows}):
            subset = [
                row for row in history_rows if row["dataset"] == dataset_name
            ]
            plt.figure()
            plt.plot(
                [row["iteration"] for row in subset],
                [row["conflict_cost"] for row in subset],
                label="Conflict cost",
            )
            plt.plot(
                [row["iteration"] for row in subset],
                [row["best_conflict_cost"] for row in subset],
                label="Best-so-far cost",
            )
            plt.xlabel("Iteration")
            plt.ylabel("Hard-conflict cost")
            plt.title(f"Min-Conflicts Cost vs Iterations: {dataset_name}")
            plt.legend()
            plt.tight_layout()
            safe_name = dataset_name.replace("/", "_")
            plt.savefig(OUTPUT / f"min_conflicts_cost_{safe_name}.png", dpi=160)
            plt.close()

    print(f"\nResults written to: {OUTPUT}")


if __name__ == "__main__":
    main()
