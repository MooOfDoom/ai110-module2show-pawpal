# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Features

- **Priority-based daily planning:** due, uncompleted tasks are ranked by priority (high first), then preferred start time, then shortest duration.
- **Earliest-free-slot placement:** each task goes in the earliest gap that fits the day window, its category window, quiet hours and tasks already placed. The plan is sequential across all pets, so the owner never does two things at once.
- **Soft preferred times:** a task gets its preferred start if it is free. Otherwise it moves to the next free slot, and the plan says so ("preferred time 07:40 was unavailable").
- **Sorting by time:** `sort_tasks_by_time` orders tasks chronologically by preferred start. Untimed tasks go last, and ties keep their input order.
- **Filtering:** `filter_tasks` narrows tasks by pet name (case-insensitive) and/or completion status, and the filters combine.
- **Conflict warnings:** `detect_conflicts` sorts timed tasks by start and compares each with the earlier task that ends latest. Overlaps are reported, for the same pet or across pets. Back-to-back tasks are not flagged. It only warns and never raises or drops a task.
- **Daily and weekly recurrence:** completing a DAILY or WEEKLY task creates the next occurrence (`+1 day` or `+7 days` with `timedelta`, so month, year and leap-day rollovers work). Completing a task twice creates no duplicate.
- **Due-date handling:** a task is hidden until its `due_date`, and weekly tasks only appear on their weekday.
- **Explained plans:** every scheduled task has a reason, and every skipped task says why it did not fit.
- **Input validation:** zero durations, out-of-range start times, weekly tasks without a weekday, and duplicate pet or task names are rejected with a clear message.
- **Editable tasks:** tasks can be edited or removed, and edits are re-validated.

## Implementation summary

The core logic lives in `pawpal_system.py` (design in `uml_diagram.md`). `main.py` is a terminal demo and `tests/test_pawpal.py` holds the tests.

- **Owner** holds the day window (`day_start`–`day_end`), `Preferences` (category time windows, quiet hours) and a list of pets. `get_all_tasks()` returns `(Pet, Task)` pairs.
- **Pet** owns its list of **Tasks** and can add (rejecting duplicates), edit and remove them.
- **Task** is a dataclass with duration, `Priority`, an optional preferred start, and a `Frequency` (once, daily, weekly). It validates itself and tracks completion per date.
- **Scheduler** takes an owner and `generate_plan(day)` reads every pet's tasks through the owner. It keeps tasks that are due and not yet completed, ranks them by priority, then preferred start, then shortest duration, and puts each into the earliest free slot. Slots respect the day window, category windows, quiet hours and tasks already placed, so the plan is sequential across all pets.
- **DailyPlan** is the result: `ScheduledItem`s (task, pet, start/end, reason) plus a `skipped` list with the reason each task didn't fit. `summary()` and `explain()` produce the text for the terminal or the Streamlit UI.

Times are stored as minutes since midnight. A preferred start is a soft preference: if that time is taken, the task moves to the next free slot.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
>python main.py
==================================================
Today's Schedule for Jordan (07:00-21:00)
==================================================
Plan for 2026-10-18 (90 min scheduled):
  07:30-08:00  Buddy: Morning walk [HIGH]
  08:00-08:10  Whiskers: Breakfast [HIGH]
  09:00-09:05  Whiskers: Give medication [HIGH]
  17:00-17:25  Whiskers: Laser pointer play [MEDIUM]
  18:00-18:20  Buddy: Brush coat [LOW]

Why these tasks:
  - Buddy / Morning walk: high priority, scheduled at 07:30 (preferred time 07:30 honored)
  - Whiskers / Breakfast: high priority, scheduled at 08:00 (preferred time 08:00 honored)
  - Whiskers / Give medication: high priority, scheduled at 09:00 (preferred time 09:00 honored)
  - Whiskers / Laser pointer play: medium priority, scheduled at 17:00 (preferred time 17:00 honored)
  - Buddy / Brush coat: low priority, scheduled at 18:00 (preferred time 18:00 honored)
```

## 🧪 Testing PawPal+

Run the full test suite from the project root:

```bash
python -m pytest
```

The tests in [tests/test_pawpal.py](tests/test_pawpal.py) cover:

- **Task basics:** marking a task complete, and adding a task to a pet.
- **Sorting:** tasks come back in chronological order with untimed tasks last. Ties keep their input order, and a task at midnight (00:00) sorts first.
- **Filtering:** by pet name (case-insensitive, and a blank name means no filter), by completion status, and both combined.
- **Recurrence:**
  - Completing a daily or weekly task creates the next occurrence (+1 day or +7 days).
  - Month, year and leap-day rollovers work.
  - Completing a task twice creates no duplicate, and an unknown task id raises `KeyError`.
  - The scheduler skips a completed recurring task until its next due date.
- **Conflict detection:**
  - Duplicate times are flagged across pets and for the same pet.
  - Partial overlaps and long tasks are flagged, but back-to-back and untimed tasks are not.
  - Completed tasks are ignored, and tasks running past midnight don't crash.
- **Edge cases:** an owner with no pets or a pet with no tasks, task validation (zero duration, out-of-range start, weekly task without a weekday), tasks that don't fit the day window, and duplicate pet or task names.

Example of a successful run:

```text
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Dev\CodePath\AI110\ai110-module2show-pawpal
plugins: anyio-4.8.0
collected 33 items

tests\test_pawpal.py .................................                   [100%]

============================= 33 passed in 0.08s ==============================
```

## 📐 Smarter Scheduling

All of these live on `Scheduler`, `Task` and `Pet` in `pawpal_system.py`, are demonstrated in `main.py`, and are covered by `tests/test_pawpal.py`.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Sorting by time | `Scheduler.sort_tasks_by_time()` | Chronological by `preferred_start`; untimed tasks last |
| Filtering | `Scheduler.filter_tasks()` | By pet name and/or completion status |
| Conflict detection | `Scheduler.detect_conflicts()` | Warns on overlapping preferred times, never raises |
| Recurring tasks | `Pet.complete_task()`, `Task.mark_complete()`, `Task.next_occurrence()` | Daily = +1 day, weekly = +7 days |

### Sorting by time

`sort_tasks_by_time(pairs)` takes `(Pet, Task)` pairs and returns them ordered by `preferred_start` (minutes since midnight) using `sorted()` with a lambda key. Tasks with no preferred time sort last, and ties keep their input order. It works on any list of pairs, so it combines with filtering.

### Filtering

`filter_tasks(pet_name=None, completed=None, day=None)` returns `(Pet, Task)` pairs.

- `pet_name` matches a pet case-insensitively. An unknown name returns an empty list.
- `completed=True` keeps finished tasks and `completed=False` keeps pending ones. `None` applies no status filter.
- The filters combine, e.g. `filter_tasks("Whiskers", completed=False)`.

### Conflict detection

`detect_conflicts(day=None)` returns a list of warning strings, one per overlapping pair, and an empty list when there are none. It never raises, so the app keeps working.

- It looks at tasks due that day and not yet completed that have a preferred start, whether they belong to the same pet or different pets.
- Tasks are sorted by start time. Each is compared with the earlier task that ends latest, and it overlaps if it starts before that task ends. Back-to-back tasks (one ends when the next starts) are not conflicts, and a long task is flagged against every task it covers.
- Warnings say whether the clash is "for the same pet" or "across pets" and show both time ranges.
- `generate_plan()` stores the warnings in `DailyPlan.warnings`, and `explain()` prints them. Detection only reports: the plan itself still places each task in a free slot, so a clashing task is moved rather than dropped.

### Recurring tasks

Each occurrence of a DAILY or WEEKLY task is its own `Task` with a `due_date`. Completing one creates the next.

- `Pet.complete_task(task_id, day)` marks the task done and appends the next occurrence to the pet. This is the method to call.
- `Task.mark_complete(day)` records the completion and returns the next occurrence, or `None` for a ONCE task or one already completed, so repeat calls never create duplicates.
- `Task.next_occurrence(day)` builds the copy using `timedelta`: `day + timedelta(days=1)` for DAILY and `day + timedelta(weeks=1)` for WEEKLY. `timedelta` handles month and year ends, e.g. 2026-12-31 becomes 2027-01-01. The copy gets a new id and empty completion history, and a WEEKLY copy's `weekday` follows its new due date.
- `Task.is_due(day)` hides a task until its `due_date`, so a completed daily task drops out of today's plan and reappears tomorrow. An uncompleted recurring task stays due on later days until it is done.

## 📸 Demo Walkthrough

### The app

Start it with `streamlit run app.py`. The page runs top to bottom:

- **Owner:** edit the owner's name.
- **Add a Pet:** enter a name and species (dog, cat or other). Duplicate pet names are rejected.
- **Tasks:** choose a pet, then set a title, category, duration, priority and frequency (once, daily or weekly, with a weekday for weekly). Optionally set a preferred start time.
- **Your Tasks:** a table of everything entered. Dropdowns filter by pet and status (all, pending, completed) and sort by time added or preferred time. A warning appears here as soon as two tasks' preferred times overlap.
- **Edit or remove a task:** pick a task, change any field and save, or remove it. Saving or removing clears the old schedule.
- **Build Schedule:** "Generate schedule" produces today's plan, with a reason for each task.

### Example workflow

1. Add a pet, e.g. **Mochi** the dog.
2. Add a task: "Morning walk", 30 min, high priority, preferred start 07:30.
3. Add a second task, "Vet call", 15 min, medium priority, preferred start 07:40. A yellow warning now says the two overlap.
4. In **Your Tasks**, set *Sort by* to "Preferred time" and filter to Mochi to see her tasks in order.
5. Click **Generate schedule**. A banner shows how many tasks fit, followed by the plan table (time, pet, task, priority, why). The walk keeps 07:30 and the vet call moves to 08:00, and the "why" column says its preferred time was unavailable.
6. If the day is too full, tasks that did not fit appear under **Could not schedule** with the reason.

### Scheduler behaviors on show

- **Sorting:** the task table reorders chronologically, with untimed tasks last.
- **Filtering:** by pet and by status.
- **Conflict warnings:** shown while you add tasks and again with the plan. The lower-priority task is moved to the next free slot, not dropped.
- **Explanations:** each row of the plan says why it was placed where it was.
- **Recurrence:** the frequency is set in the UI. Completing a recurring task and generating its next occurrence is done in code (`Pet.complete_task`), and `main.py` and the tests exercise it.

### Sample CLI output

Excerpt from `python main.py` (the plan is for the day it is run):

```text
Sorted by time:
  07:30  Buddy     Morning walk         [pending]
  07:40  Buddy     Vet call             [pending]
  08:00  Whiskers  Breakfast            [done]
  08:00  Whiskers  Breakfast            [pending]
  09:00  Whiskers  Give medication      [done]
  17:00  Whiskers  Laser pointer play   [pending]
  17:10  Buddy     Training             [pending]
  18:00  Buddy     Brush coat           [pending]
  --:--  Buddy     Feed dinner          [pending]


[...filter output omitted...]

Conflict check:
  WARNING: Conflict for the same pet: Buddy's 'Morning walk' (07:30-08:00) overlaps Buddy's 'Vet call' (07:40-07:55)
  WARNING: Conflict across pets: Whiskers's 'Laser pointer play' (17:00-17:25) overlaps Buddy's 'Training' (17:10-17:30)

==================================================
Today's Schedule for Jordan (07:00-21:00)
==================================================
Plan for 2026-10-18 (120 min scheduled):
  07:00-07:10  Buddy: Feed dinner [MEDIUM]
  07:30-08:00  Buddy: Morning walk [HIGH]
  08:00-08:15  Buddy: Vet call [MEDIUM]
  17:00-17:25  Whiskers: Laser pointer play [MEDIUM]
  17:25-17:45  Buddy: Training [LOW]
  18:00-18:20  Buddy: Brush coat [LOW]

Why these tasks:
  - Buddy / Feed dinner: medium priority, scheduled at 07:00
  - Buddy / Morning walk: high priority, scheduled at 07:30 (preferred time 07:30 honored)
  - Buddy / Vet call: medium priority, scheduled at 08:00 (preferred time 07:40 was unavailable)
  - Whiskers / Laser pointer play: medium priority, scheduled at 17:00 (preferred time 17:00 honored)
  - Buddy / Training: low priority, scheduled at 17:25 (preferred time 17:10 was unavailable)
  - Buddy / Brush coat: low priority, scheduled at 18:00 (preferred time 18:00 honored)

Warnings:
  ! Conflict for the same pet: Buddy's 'Morning walk' (07:30-08:00) overlaps Buddy's 'Vet call' (07:40-07:55)
  ! Conflict across pets: Whiskers's 'Laser pointer play' (17:00-17:25) overlaps Buddy's 'Training' (17:10-17:30)
```
