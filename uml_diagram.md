# PawPal+ UML Class Diagram

Times are stored as minutes since midnight.

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
        +dict category_windows
        +list quiet_hours
    }

    class Pet {
        +str name
        +str species
        +int age
        +str notes
        +list~Task~ tasks
        +add_task(task: Task) void
        +edit_task(task_id: str, **changes) void
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
        +set~date~ completed_on
        +is_due(day: date) bool
        +is_completed(day: date) bool
        +mark_complete(day: date) void
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
        -due_tasks(day: date) list~tuple~
        -rank_tasks(pairs: list) list
        -find_slot(task: Task, cursor: int) int
        -explain_choice(pet: Pet, task: Task, scheduled: bool) str
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
        +list~tuple~ skipped
        +total_minutes() int
        +summary() str
        +explain() str
    }

    Owner "1" *-- "0..*" Pet : owns
    Owner *-- Preferences : has
    Pet "1" *-- "0..*" Task : has
    Task --> Priority : uses
    Task --> Frequency : repeats
    Scheduler --> Owner : plans for
    Scheduler ..> DailyPlan : creates
    DailyPlan "1" *-- "0..*" ScheduledItem : contains
    ScheduledItem --> Task : snapshot of
    ScheduledItem --> Pet : for
```

## Notes
- **Owner** defines the day window (`day_start`–`day_end`) and holds typed **Preferences** (per-category time windows, quiet hours). `get_all_tasks()` returns `(Pet, Task)` pairs so the pet is never lost.
- **Task** is validated on creation (duration > 0, valid times, weekday required for weekly). Recurrence is modeled with `Frequency`; completion is tracked per date in `completed_on`.
- **Scheduler** produces one sequential plan across all pets (the owner does one thing at a time). Ranking: priority, then preferred start, then shortest duration. The last plan is kept on `Scheduler.plan`; the Streamlit app should hold the `Owner`/`Scheduler` in `st.session_state`.
- **ScheduledItem** is a snapshot; editing a task later does not change an existing plan.
- **DailyPlan** lists skipped tasks with the reason each was skipped.
