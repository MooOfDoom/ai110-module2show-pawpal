"""PawPal+ core system: Owner, Pet, Task and the Scheduler that plans a day.

Times are stored as minutes since midnight (e.g. 8:30 AM -> 510).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, replace
from datetime import date as Date
from datetime import timedelta
from enum import Enum

MINUTES_PER_DAY = 24 * 60


def format_time(minutes: int) -> str:
    """Convert minutes since midnight to 'HH:MM'."""
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class Frequency(Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"


@dataclass
class Task:
    """A single care task for a pet."""

    title: str
    category: str
    duration_minutes: int
    priority: Priority = Priority.MEDIUM
    preferred_start: int | None = None  # minutes since midnight
    frequency: Frequency = Frequency.ONCE
    weekday: int | None = None  # 0=Mon..6=Sun, used for WEEKLY tasks
    due_date: Date | None = None  # not due before this day; None means due immediately
    completed_on: set[Date] = field(default_factory=set)
    id: str = field(default_factory=lambda: uuid.uuid4().hex)

    def __post_init__(self) -> None:
        """Reject invalid durations, start times and weekly tasks without a weekday."""
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be greater than 0")
        if self.preferred_start is not None and not 0 <= self.preferred_start < MINUTES_PER_DAY:
            raise ValueError("preferred_start must be between 0 and 1439")
        if self.frequency is Frequency.WEEKLY and (
            self.weekday is None or not 0 <= self.weekday <= 6
        ):
            raise ValueError("WEEKLY tasks need a weekday between 0 (Mon) and 6 (Sun)")

    def is_due(self, day: Date) -> bool:
        """Whether this task should appear in the plan for `day`.

        Args:
            day: The date being planned.

        Returns:
            False before `due_date`. WEEKLY tasks are due only on their `weekday`. ONCE and
            DAILY tasks are due from `due_date` (or immediately) until completed.
        """
        if self.due_date is not None and day < self.due_date:
            return False
        if self.frequency is Frequency.WEEKLY:
            return day.weekday() == self.weekday
        return True  # ONCE and DAILY: due from due_date until completed

    def is_completed(self, day: Date) -> bool:
        """Whether this task instance has been completed.

        Each recurrence is its own Task instance, so any entry in `completed_on` means done.
        `day` is accepted for a consistent interface with `is_due` but is not used.
        """
        return bool(self.completed_on)

    def next_occurrence(self, day: Date) -> Task | None:
        """Build the next occurrence of a recurring task.

        DAILY tasks are due `day + timedelta(days=1)` and WEEKLY tasks `day + timedelta(weeks=1)`.
        timedelta does the calendar maths, so month and year ends roll over correctly
        (2026-12-31 -> 2027-01-01). A WEEKLY copy's `weekday` follows its new due date.

        Args:
            day: The date the current instance was completed.

        Returns:
            A copy with a new id, empty `completed_on` and the new `due_date`, or None for
            a ONCE task.
        """
        if self.frequency is Frequency.DAILY:
            next_day = day + timedelta(days=1)
        elif self.frequency is Frequency.WEEKLY:
            next_day = day + timedelta(weeks=1)
        else:
            return None
        return replace(
            self,
            due_date=next_day,
            weekday=next_day.weekday() if self.frequency is Frequency.WEEKLY else self.weekday,
            completed_on=set(),
            id=uuid.uuid4().hex,
        )

    def mark_complete(self, day: Date) -> Task | None:
        """Record completion on `day` and create the next occurrence if the task recurs.

        Args:
            day: The date the task was completed.

        Returns:
            The next occurrence for DAILY/WEEKLY tasks, or None for ONCE tasks and for a task
            that was already completed (so repeat calls never create duplicates). The caller
            must store the returned task; `Pet.complete_task` does this.
        """
        if self.completed_on:
            return None
        self.completed_on.add(day)
        return self.next_occurrence(day)


@dataclass
class Pet:
    """A pet and the care tasks that belong to it."""

    name: str
    species: str
    age: int = 0
    notes: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task; reject duplicates (same title + category)."""
        key = (task.title.strip().lower(), task.category.strip().lower())
        for existing in self.tasks:
            if (existing.title.strip().lower(), existing.category.strip().lower()) == key:
                raise ValueError(f"{self.name} already has a '{task.title}' ({task.category}) task")
        self.tasks.append(task)

    def edit_task(self, task_id: str, **changes) -> None:
        """Update fields of the task with `task_id`, re-validating the result."""
        if "id" in changes:
            raise ValueError("A task's id cannot be changed")
        for i, task in enumerate(self.tasks):
            if task.id == task_id:
                # replace() re-runs __post_init__, so edits are validated too
                self.tasks[i] = replace(task, **changes)
                return
        raise KeyError(f"No task with id {task_id}")

    def complete_task(self, task_id: str, day: Date) -> Task | None:
        """Complete a task and automatically add its next occurrence to this pet.

        Args:
            task_id: Id of the task to complete.
            day: The date it was completed; the next DAILY task is due `day + 1 day`.

        Returns:
            The newly added task, or None if the task does not recur or was already done.

        Raises:
            KeyError: If no task has `task_id`.
        """
        for task in self.tasks:
            if task.id == task_id:
                next_task = task.mark_complete(day)
                if next_task is not None:
                    self.tasks.append(next_task)
                return next_task
        raise KeyError(f"No task with id {task_id}")

    def remove_task(self, task_id: str) -> None:
        """Remove the task with `task_id`, raising KeyError if it does not exist."""
        for i, task in enumerate(self.tasks):
            if task.id == task_id:
                del self.tasks[i]
                return
        raise KeyError(f"No task with id {task_id}")


@dataclass
class Preferences:
    """Owner preferences the Scheduler reads."""

    # category -> (earliest_start, latest_end) in minutes since midnight
    category_windows: dict[str, tuple[int, int]] = field(default_factory=dict)
    # (start, end) blocks where nothing may be scheduled
    quiet_hours: list[tuple[int, int]] = field(default_factory=list)


@dataclass
class Owner:
    """The pet owner: their day window, preferences and pets."""

    name: str
    day_start: int = 8 * 60  # minutes since midnight
    day_end: int = 20 * 60
    preferences: Preferences = field(default_factory=Preferences)
    pets: list[Pet] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Reject day windows that are empty or outside 0-1440 minutes."""
        if not 0 <= self.day_start < self.day_end <= MINUTES_PER_DAY:
            raise ValueError("Need 0 <= day_start < day_end <= 1440")

    @property
    def available_minutes(self) -> int:
        """Total time in the day window (day_end - day_start)."""
        return self.day_end - self.day_start

    def add_pet(self, pet: Pet) -> None:
        """Add a pet, rejecting duplicate names."""
        if any(p.name.strip().lower() == pet.name.strip().lower() for p in self.pets):
            raise ValueError(f"{self.name} already has a pet named '{pet.name}'")
        self.pets.append(pet)

    def remove_pet(self, pet: Pet) -> None:
        """Remove a pet (and its tasks) from this owner."""
        self.pets.remove(pet)

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """All tasks paired with the pet they belong to."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]


@dataclass
class ScheduledItem:
    """A snapshot of a task placed in a plan (not updated if the task is later edited)."""

    task: Task
    pet: Pet
    start_time: int  # minutes since midnight
    end_time: int
    reason: str = ""


@dataclass
class DailyPlan:
    """The scheduler output: ordered items plus skipped tasks."""

    date: Date = field(default_factory=Date.today)
    items: list[ScheduledItem] = field(default_factory=list)
    skipped: list[tuple[Pet, Task, str]] = field(default_factory=list)  # (pet, task, why)
    warnings: list[str] = field(default_factory=list)  # e.g. conflicting preferred times

    @property
    def total_minutes(self) -> int:
        """Total minutes of scheduled tasks in this plan."""
        return sum(item.end_time - item.start_time for item in self.items)

    def summary(self) -> str:
        """Short text listing each scheduled task with its time slot."""
        if not self.items:
            return f"{self.date}: nothing scheduled."
        lines = [f"Plan for {self.date} ({self.total_minutes} min scheduled):"]
        for item in self.items:
            lines.append(
                f"  {format_time(item.start_time)}-{format_time(item.end_time)}  "
                f"{item.pet.name}: {item.task.title} [{item.task.priority.name}]"
            )
        return "\n".join(lines)

    def explain(self) -> str:
        """The summary plus the reason for each scheduled and skipped task."""
        lines = [self.summary()]
        if self.items:
            lines.append("")
            lines.append("Why these tasks:")
            for item in self.items:
                lines.append(f"  - {item.pet.name} / {item.task.title}: {item.reason}")
        if self.warnings:
            lines.append("")
            lines.append("Warnings:")
            lines.extend(f"  ! {w}" for w in self.warnings)
        if self.skipped:
            lines.append("")
            lines.append("Skipped:")
            for pet, task, why in self.skipped:
                lines.append(f"  - {pet.name} / {task.title}: {why}")
        return "\n".join(lines)


class Scheduler:
    """Builds a sequential (one task at a time, across all pets) daily plan.

    Ranking order: priority (high first), then preferred_start, then shortest duration.
    Each task goes in the earliest free slot, so a short task can fill a gap left
    by a task that was pushed later by its preferred start.
    """

    def __init__(self, owner: Owner) -> None:
        """Create a scheduler that plans for `owner`."""
        self.owner = owner
        self.plan: DailyPlan | None = None  # last generated plan; keep in st.session_state

    def generate_plan(self, day: Date | None = None) -> DailyPlan:
        """Build and store a plan for `day` (default today) from all of the owner's tasks."""
        day = day or Date.today()
        plan = DailyPlan(date=day)
        plan.warnings = self.detect_conflicts(day)
        busy: list[tuple[int, int]] = list(self.owner.preferences.quiet_hours)

        for pet, task in self._rank_tasks(self._due_tasks(day)):
            start = self._find_slot(task, busy)
            reason = self._explain_choice(pet, task, start)
            if start is None:
                plan.skipped.append((pet, task, reason))
                continue
            end = start + task.duration_minutes
            busy.append((start, end))
            plan.items.append(ScheduledItem(task, pet, start, end, reason))

        plan.items.sort(key=lambda item: item.start_time)
        self.plan = plan
        return plan

    def sort_tasks_by_time(self, pairs: list[tuple[Pet, Task]]) -> list[tuple[Pet, Task]]:
        """Sort (pet, task) pairs chronologically by preferred start.

        Args:
            pairs: (Pet, Task) pairs, e.g. from `owner.get_all_tasks()` or `filter_tasks`.

        Returns:
            A new list ordered by `preferred_start` (minutes since midnight). Tasks without
            a preferred time go last. The sort is stable, so ties keep their input order.
        """
        return sorted(
            pairs,
            key=lambda pt: pt[1].preferred_start
            if pt[1].preferred_start is not None
            else MINUTES_PER_DAY,
        )

    def filter_tasks(
        self,
        pet_name: str | None = None,
        completed: bool | None = None,
        day: Date | None = None,
    ) -> list[tuple[Pet, Task]]:
        """Filter the owner's tasks by pet name and/or completion status.

        Args:
            pet_name: Keep only this pet's tasks (case-insensitive, surrounding spaces
                ignored). None or a blank string keeps all pets.
            completed: True keeps completed tasks, False keeps pending ones, None keeps both.
            day: The date used for the completion check (default today).

        Returns:
            (Pet, Task) pairs in owner order. Filters combine with AND, and the result is
            empty if nothing matches (an unknown pet is not an error).
        """
        day = day or Date.today()
        name = (pet_name or "").strip().lower() or None
        return [
            (pet, task)
            for pet, task in self.owner.get_all_tasks()
            if (name is None or pet.name.strip().lower() == name)
            and (completed is None or task.is_completed(day) == completed)
        ]

    def detect_conflicts(self, day: Date | None = None) -> list[str]:
        """Warn about pending tasks whose preferred time slots overlap.

        Lightweight strategy: sort tasks (same pet or different pets) by preferred start,
        then compare each with the earlier task that ends latest. It overlaps when it starts
        before that task ends, so a long task is flagged against every task it covers while
        back-to-back tasks are not. This is O(n log n) and only reports; it never raises
        and never changes the plan.

        Args:
            day: The date to check (default today). Only tasks due and not completed that
                day with a preferred start are considered.

        Returns:
            One warning string per overlapping pair, or an empty list if none.
        """
        day = day or Date.today()
        timed = sorted(
            (
                (task.preferred_start, task.preferred_start + task.duration_minutes, pet, task)
                for pet, task in self._due_tasks(day)
                if task.preferred_start is not None
            ),
            key=lambda t: t[:2],
        )
        warnings: list[str] = []
        latest = None  # the earlier task that ends last
        for current in timed:
            if latest is not None and current[0] < latest[1]:
                warnings.append(self._conflict_message(latest, current))
            if latest is None or current[1] > latest[1]:
                latest = current
        return warnings

    @staticmethod
    def _conflict_message(a: tuple, b: tuple) -> str:
        """Format a warning for two overlapping (start, end, pet, task) entries.

        `a` starts first. The message says whether the pets are the same and shows both
        time ranges as HH:MM-HH:MM.
        """
        where = "for the same pet" if a[2] is b[2] else "across pets"
        return (
            f"Conflict {where}: {a[2].name}'s '{a[3].title}' ({format_time(a[0])}-"
            f"{format_time(a[1])}) overlaps {b[2].name}'s '{b[3].title}' "
            f"({format_time(b[0])}-{format_time(b[1])})"
        )

    def _due_tasks(self, day: Date) -> list[tuple[Pet, Task]]:
        """Tasks due on `day` and not yet completed, read from the owner."""
        return [
            (pet, task)
            for pet, task in self.owner.get_all_tasks()
            if task.is_due(day) and not task.is_completed(day)
        ]

    def _rank_tasks(self, pairs: list[tuple[Pet, Task]]) -> list[tuple[Pet, Task]]:
        """Sort by priority (high first), then preferred start, then shortest duration."""
        return sorted(
            pairs,
            key=lambda pt: (
                -pt[1].priority.value,
                pt[1].preferred_start if pt[1].preferred_start is not None else MINUTES_PER_DAY,
                pt[1].duration_minutes,
            ),
        )

    def _find_slot(self, task: Task, busy: list[tuple[int, int]]) -> int | None:
        """Earliest start that fits the day window, category window and avoids `busy` blocks.

        The preferred start is tried first as a lower bound; if nothing fits after it,
        the search falls back to the beginning of the window.
        """
        lo = self.owner.day_start
        hi = self.owner.day_end
        window = self.owner.preferences.category_windows.get(task.category)
        if window:
            lo, hi = max(lo, window[0]), min(hi, window[1])

        if task.preferred_start is not None:
            slot = self._first_gap(max(lo, task.preferred_start), hi, task.duration_minutes, busy)
            if slot is not None:
                return slot
        return self._first_gap(lo, hi, task.duration_minutes, busy)

    @staticmethod
    def _first_gap(lo: int, hi: int, duration: int, busy: list[tuple[int, int]]) -> int | None:
        """First start in [lo, hi] where `duration` minutes fit without touching `busy` blocks."""
        start = lo
        for b_start, b_end in sorted(busy):
            if b_end <= start:
                continue
            if start + duration <= b_start:
                break
            start = max(start, b_end)
        return start if start + duration <= hi else None

    def _explain_choice(self, pet: Pet, task: Task, start: int | None) -> str:
        """Why a task was scheduled at `start`, or skipped when `start` is None."""
        if start is None:
            return (
                f"no {task.duration_minutes}-minute slot left between "
                f"{format_time(self.owner.day_start)} and {format_time(self.owner.day_end)} "
                f"(after higher-priority tasks, quiet hours and time windows)"
            )
        reason = f"{task.priority.name.lower()} priority, scheduled at {format_time(start)}"
        if task.preferred_start is not None:
            if start == task.preferred_start:
                reason += f" (preferred time {format_time(task.preferred_start)} honored)"
            else:
                reason += f" (preferred time {format_time(task.preferred_start)} was unavailable)"
        return reason
