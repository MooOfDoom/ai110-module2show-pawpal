# PawPal+ UML Class Diagram

Times are stored as minutes since midnight. Source of truth for the diagram is `diagrams/uml.mmd`.

```mermaid
classDiagram
    class Owner {
        +str name
        +int day_start
        +int day_end
        +Preferences preferences
        +list~Pet~ pets
        +available_minutes() int
        +add_pet(pet: Pet) void
        +remove_pet(pet: Pet) void
        +get_all_tasks() list~tuple~Pet, Task~~
    }

    class Preferences {
        +dict~str, tuple~int,int~~ category_windows
        +list~tuple~int,int~~ quiet_hours
    }

    class Pet {
        +str name
        +str species
        +int age
        +str notes
        +list~Task~ tasks
        +add_task(task: Task) void
        +edit_task(task_id: str, **changes) void
        +complete_task(task_id: str, day: date) Task
        +remove_task(task_id: str) void
    }

    class Task {
        +str id
        +str title
        +str category
        +int duration_minutes
        +Priority priority
        +int preferred_start
        +Frequency frequency
        +int weekday
        +date due_date
        +set~date~ completed_on
        +is_due(day: date) bool
        +is_completed(day: date) bool
        +next_occurrence(day: date) Task
        +mark_complete(day: date) Task
    }

    class Priority {
        <<enumeration>>
        LOW
        MEDIUM
        HIGH
    }

    class Frequency {
        <<enumeration>>
        ONCE
        DAILY
        WEEKLY
    }

    class Scheduler {
        +Owner owner
        +DailyPlan plan
        +generate_plan(day: date) DailyPlan
        +sort_tasks_by_time(pairs: list) list
        +filter_tasks(pet_name: str, completed: bool, day: date) list
        +detect_conflicts(day: date) list~str~
        -conflict_message(a: tuple, b: tuple) str$
        -due_tasks(day: date) list~tuple~
        -rank_tasks(pairs: list) list
        -find_slot(task: Task, busy: list) int
        -first_gap(lo: int, hi: int, duration: int, busy: list) int$
        -explain_choice(pet: Pet, task: Task, start: int) str
    }

    class ScheduledItem {
        +Task task
        +Pet pet
        +int start_time
        +int end_time
        +str reason
    }

    class DailyPlan {
        +date date
        +list~ScheduledItem~ items
        +list~tuple~Pet, Task, str~~ skipped
        +list~str~ warnings
        +total_minutes() int
        +summary() str
        +explain() str
    }

    class StreamlitUI {
        <<app.py>>
        owner and plan kept in st.session_state
    }

    Owner "1" *-- "0..*" Pet : owns
    Owner *-- Preferences : has
    Pet "1" *-- "0..*" Task : has
    Pet ..> Task : appends next occurrence
    Task --> Priority : uses
    Task --> Frequency : repeats
    Task ..> Task : next_occurrence creates
    Scheduler --> Owner : plans for
    Scheduler ..> Preferences : reads quiet_hours / category_windows
    Scheduler --> DailyPlan : last plan
    Scheduler ..> DailyPlan : creates (warnings from detect_conflicts)
    Scheduler ..> ScheduledItem : creates
    DailyPlan "1" *-- "0..*" ScheduledItem : contains
    DailyPlan ..> Pet : skipped refers to
    DailyPlan ..> Task : skipped refers to
    ScheduledItem --> Task : snapshot of
    ScheduledItem --> Pet : for
    StreamlitUI ..> Owner : edits and reads
    StreamlitUI ..> Pet : add / edit / remove tasks
    StreamlitUI ..> Scheduler : public methods only
    StreamlitUI ..> DailyPlan : displays
```

## Notes
- **Owner** defines the day window (`day_start`-`day_end`) and holds typed **Preferences** (per-category time windows, quiet hours). `get_all_tasks()` returns `(Pet, Task)` pairs so the pet is never lost.
- **Task** is validated on creation (duration > 0, valid times, weekday required for weekly). Recurrence is modeled with `Frequency`; each recurrence is its own `Task`. `mark_complete` records the date and returns the next occurrence (new id, new `due_date`), which `Pet.complete_task` appends to the pet.
- **Pet** manages its tasks: add (rejects duplicates), edit (re-validated through `dataclasses.replace`), complete and remove.
- **Scheduler** produces one sequential plan across all pets (the owner does one thing at a time). Ranking: priority, then preferred start, then shortest duration. It also offers `sort_tasks_by_time`, `filter_tasks` and `detect_conflicts`, which only report overlapping preferred times and never change the plan. Private helpers are shown with `-` (`$` marks static ones). The last plan is kept on `Scheduler.plan`.
- **ScheduledItem** holds a reference to the task at planning time. Editing a task replaces it in `pet.tasks`, so an existing plan keeps the old object and is stale.
- **DailyPlan** lists skipped tasks with the reason each was skipped and carries `warnings` from conflict detection.
- **StreamlitUI** (`app.py`) is a client, not part of the domain model. It calls only the public methods, keeps the `Owner` and latest plan in `st.session_state`, and clears the plan after a task is edited or removed.
