"""PawPal+ core system: class skeletons based on uml_diagram.md."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date as Date
from enum import Enum


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


@dataclass
class Task:
    title: str
    category: str
    duration_minutes: int
    priority: Priority = Priority.MEDIUM
    preferred_time: str = ""
    completed: bool = False
    id: str = field(default_factory=lambda: uuid.uuid4().hex)

    def mark_complete(self) -> None:
        pass


@dataclass
class Pet:
    name: str
    species: str
    age: int = 0
    notes: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        pass

    def edit_task(self, task_id: str, **changes) -> None:
        pass

    def remove_task(self, task_id: str) -> None:
        pass


@dataclass
class Owner:
    name: str
    available_minutes: int
    preferences: dict = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        pass

    def remove_pet(self, pet: Pet) -> None:
        pass

    def get_all_tasks(self) -> list[Task]:
        pass


@dataclass
class ScheduledItem:
    task: Task
    pet: Pet
    start_time: str
    end_time: str
    reason: str = ""


@dataclass
class DailyPlan:
    date: Date = field(default_factory=Date.today)
    items: list[ScheduledItem] = field(default_factory=list)
    skipped_tasks: list[Task] = field(default_factory=list)

    @property
    def total_minutes(self) -> int:
        pass

    def summary(self) -> str:
        pass

    def explain(self) -> str:
        pass


class Scheduler:
    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def generate_plan(self) -> DailyPlan:
        pass

    def _rank_tasks(self, tasks: list[Task]) -> list[Task]:
        pass

    def _fits_in_time(self, task: Task, remaining: int) -> bool:
        pass

    def _explain_choice(self, task: Task, scheduled: bool) -> str:
        pass
