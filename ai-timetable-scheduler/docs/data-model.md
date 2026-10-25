# Data Model

## 1. Subject
- `code`: unique subject identifier.
- `name`: subject name.
- `weekly_hours`: required weekly teaching periods.
- `type`: `theory` or `lab`.

## 2. Teacher
- `id`: unique teacher identifier.
- `name`: teacher name.
- `subjects`: subjects the teacher is qualified to teach.
- `unavailable_slots`: day/period combinations the teacher cannot teach.
- `max_weekly_load`: maximum permitted weekly teaching periods.

## 3. Class or Batch
- `id`: unique class identifier.
- `name`: class name.
- `strength`: number of students.
- `subjects`: subjects required by the class.
- `lunch_break_slot`: assigned lunch period.

## 4. Room
- `id`: unique room identifier.
- `name`: room name.
- `capacity`: maximum student capacity.
- `type`: `classroom` or `lab`.

## 5. Time Slot
- `id`: unique slot identifier.
- `day`: working day.
- `period`: period number.
- `is_break`: whether the slot is a break.

## 6. Teaching Session
Each required session becomes a scheduling variable.

- `id`: unique session identifier.
- `class_id`: class requiring the session.
- `subject_code`: required subject.
- `teacher_id`: assigned qualified teacher.
- `duration`: number of consecutive periods required.
- `room_id`: room assigned after scheduling.
- `start_slot_id`: assigned starting slot.

For a lab that lasts multiple periods, represent its duration explicitly and reserve all consecutive periods.

## 7. Timetable Assignment
An assignment connects a session to:
- Teacher.
- Class.
- Room.
- Day and period or consecutive time slots.

## 8. Solver Result
- `algorithm`: algorithm name.
- `status`: success, no solution, timeout, or invalid input.
- `assignments`: resulting schedule.
- `runtime_seconds`: measured runtime.
- `hard_violations`: independent violation count.
- `soft_penalty`: calculated quality penalty.
- `nodes_expanded` or `iterations`: search effort.
- `seed`: random seed where applicable.

## 9. Relationships and Validation
- A class requires one or more subjects.
- A teacher can teach only qualified subjects.
- A session belongs to one class and one subject.
- A session is assigned a qualified teacher and a compatible room.
- A room must have enough capacity for the class.
- Sessions must respect teacher availability, lunch breaks, weekly hours, and workload limits.

Use the same field names throughout loaders, solvers, validators, exports, and tests. If the implementation chooses different names, update this document to match the actual code.