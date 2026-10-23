# Timetable Solver Experiment Analysis

## Experimental setup

Five solvers were evaluated on two timetable datasets: a small dataset containing 3 classes, 6 teachers and 4 rooms, and a larger dataset containing 8 classes, 15 teachers and 8 rooms. Both use a five-day working week. Basic and heuristic backtracking were each run once per dataset, while Min-Conflicts, Simulated Annealing and Hybrid were each run ten times. Performance was measured using runtime, hard-constraint violations and soft-constraint penalty.

## Results and discussion

All five solvers achieved a 100% success rate on both datasets, with zero hard-constraint violations in the recorded runs. Basic backtracking was the fastest solver in these experiments, averaging approximately 0.0012 seconds on the small dataset and 0.0220 seconds on the large dataset. It explored 15 and 40 nodes respectively, with no backtracks in either run.

Heuristic backtracking also found valid timetables, but took approximately 0.0292 seconds on the small dataset and 2.1137 seconds on the large dataset. This illustrates that heuristic techniques do not necessarily reduce runtime on every problem instance; performance depends on the search strategy, domains and problem structure.

Min-Conflicts provided a useful balance between speed and soft-constraint quality. Its average runtime was approximately 0.0022 seconds on the small dataset and 0.0476 seconds on the large dataset. Its average soft penalties were 7.7 and 24.6 respectively. The recorded conflict-cost traces reached zero after four iterations on the small dataset and six iterations on the large dataset.

Simulated Annealing and Hybrid achieved an average soft penalty of zero on both datasets, indicating that their returned timetables incurred no penalty under the three soft metrics used: class gaps, subject distribution and teacher consecutive periods. However, these results came with higher runtimes. Simulated Annealing averaged 0.5492 seconds on the small dataset and 1.8883 seconds on the large dataset, while Hybrid averaged 0.1656 and 2.5606 seconds respectively.

## Conclusion and limitations

For these datasets, basic backtracking was the fastest option, Min-Conflicts offered a fast intermediate solution, and Simulated Annealing and Hybrid achieved the best measured soft-constraint quality. The larger dataset generally required more time, although two dataset sizes are insufficient to establish a general scaling trend.

The results should be interpreted cautiously: deterministic solvers were tested once per dataset, while randomized solvers were tested ten times. Further experiments on larger, more constrained and more varied datasets would provide stronger evidence about runtime, solution quality and reliability. A soft penalty of zero applies only to the implemented soft metrics and weights, not to every possible timetable preference.