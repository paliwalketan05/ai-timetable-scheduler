from dataclasses import dataclass
from src.models.entities import SchedulingProblem

@dataclass(frozen=True)
class SchedulingSession:
    """One required teaching session that must be scheduled."""

    id: str
    group_id: str
    subject_id: str
    duration_slots: int

def expand_sessions(
        problem: SchedulingProblem,
) -> list[SchedulingSession]:
    
    sessions=[]

    for group in problem.student_groups:
        for requirement in group.subject_requirements:
            for session_number in range(
                1, requirement.weekly_sessions + 1
            ):
                session = SchedulingSession(
                    id=f"{group.id}_{requirement.subject_id}_S{session_number}",
                    group_id=group.id,
                    subject_id=requirement.subject_id,
                    duration_slots=requirement.duration_slots,
                )

                sessions.append(session)
    return sessions