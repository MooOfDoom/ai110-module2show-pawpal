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

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | | e.g., by priority, duration |
| Filtering | | e.g., skip tasks if time runs out |
| Conflict handling | | e.g., overlapping time slots |
| Recurring tasks | | e.g., daily vs. weekly |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
