"""PawPal+ core system: class skeletons based on uml_diagram.md.

Times are stored as minutes since midnight (e.g. 8:30 AM -> 510).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date as Date
from enum import Enum


def format_time(minutes: int) -> str:
    """Convert minutes since midnight to 'HH:MM'."""
    pass


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
    title: str
    category: str
    duration_minutes: int
    priority: Priority = Priority.MEDIUM
    preferred_start: int | None = None  # minutes since midnight
    frequency: Frequency = Frequency.ONCE
    weekday: int | None = None  # 0=Mon..6=Sun, used for WEEKLY tasks
    completed_on: set[Date] = field(default_factory=set)
    id: str = field(default_factory=lambda: uuid.uuid4().hex)

    def __post_init__(self) -> None:
        """Validate: duration > 0, preferred_start within 0..1439, weekday set for WEEKLY."""
        pass

    def is_due(self, day: Date) -> bool:
        """Whether this task should appear in the plan for `day`."""
        pass

    def is_completed(self, day: Date) -> bool:
        pass

    def mark_complete(self, day: Date) -> None:
        pass


@dataclass
class Pet:
    name: str
    species: str
    age: int = 0
    notes: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task; reject duplicates (same title + category)."""
        pass

    def edit_task(self, task_id: str, **changes) -> None:
        pass

    def remove_task(self, task_id: str) -> None:
        pass


@dataclass
class Preferences:
    """Owner preferences the Scheduler reads."""

    # category -> (earliest_start, latest_end) in minutes since midnight
    category_windows: dict[str, tuple[int, int]] = field(default_factory=dict)
    # list of (start, end) blocks where nothing may be scheduled
    quiet_hours: list[tuple[int, int]] = field(default_factory=list)


@dataclass
class Owner:
    name: str
    day_start: int = 8 * 60  # minutes since midnight
    day_end: int = 20 * 60
    preferences: Preferences = field(default_factory=Preferences)
    pets: list[Pet] = field(default_factory=list)

    @property
    def available_minutes(self) -> int:
        """Total time in the day window (day_end - day_start)."""
        pass

    def add_pet(self, pet: Pet) -> None:
        pass

    def remove_pet(self, pet: Pet) -> None:
        pass

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """All tasks paired with the pet they belong to."""
        pass


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
    date: Date = field(default_factory=Date.today)
    items: list[ScheduledItem] = field(default_factory=list)
    skipped: list[tuple[Pet, Task, str]] = field(default_factory=list)  # (pet, task, why)

    @property
    def total_minutes(self) -> int:
        pass

    def summary(self) -> str:
        pass

    def explain(self) -> str:
        pass


class Scheduler:
    """Builds a sequential (one task at a time, across all pets) daily plan.

    Ranking order: priority (high first), then preferred_start, then shortest duration.
    """

    def __init__(self, owner: Owner) -> None:
        self.owner = owner
        self.plan: DailyPlan | None = None  # last generated plan; keep in st.session_state

    def generate_plan(self, day: Date | None = None) -> DailyPlan:
        pass

    def _due_tasks(self, day: Date) -> list[tuple[Pet, Task]]:
        """Tasks due on `day` and not yet completed."""
        pass

    def _rank_tasks(self, pairs: list[tuple[Pet, Task]]) -> list[tuple[Pet, Task]]:
        pass

    def _find_slot(self, task: Task, cursor: int) -> int | None:
        """Earliest start >= cursor that fits the day window, category window and quiet hours."""
        pass

    def _explain_choice(self, pet: Pet, task: Task, scheduled: bool) -> str:
        pass
