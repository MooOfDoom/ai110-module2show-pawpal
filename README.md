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

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
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

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
