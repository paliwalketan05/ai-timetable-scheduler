from dataclasses import dataclass

@dataclass(frozen=True)
class Assignment:
    """One candidate placement for a scheduling session."""

    session_id: str
    teacher_id: str
    day: str
    start_period: int
    room_id: str

@dataclass
class ScheduledSession:
    """A session together with its selected assignment."""

    session_id: str
    group_id: str
    subject_id: str
    duration_slots: int
    assignment: Assignment

@dataclass
class Timetable:
    """A collection of scheduled sessions."""

    sessions: list[ScheduledSession]

    def assignments(self) -> list[Assignment]:
        """return all selected assinments."""
        return [session.assignment for session in self.sessions]