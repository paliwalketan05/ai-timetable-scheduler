
from dataclasses import dataclass, field


@dataclass
class Subject:
    id: str
    name: str
    subject_type: str = "theory"


@dataclass
class SubjectRequirement:
    subject_id: str
    weekly_sessions: int
    duration_slots: int = 1


@dataclass
class Teacher:
    id: str
    name: str
    subjects_can_teach: list[str] = field(default_factory=list)
    unavailable_slots: list[str] = field(default_factory=list)
    maximum_weekly_load: int = 20


@dataclass
class StudentGroup:
    id: str
    name: str
    strength: int
    subject_requirements: list[SubjectRequirement] = field(
        default_factory=list
    )
    lunch_break_periods: list[int] = field(default_factory=list)


@dataclass
class Room:
    id: str
    name: str
    capacity: int
    room_type: str = "classroom"


@dataclass
class TimeStructure:
    working_days: list[str]
    periods_per_day: int
    break_periods: list[int] = field(default_factory=list)
    period_duration_minutes: int = 50


@dataclass
class SchedulingProblem:
    subjects: list[Subject]
    teachers: list[Teacher]
    student_groups: list[StudentGroup]
    rooms: list[Room]
    time_structure: TimeStructure
