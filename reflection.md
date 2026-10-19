# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

The initial design has a Scheduler that handles the overall scheduling tasks for an Owner who has a collection of Pets. Each Pet has a list of Tasks that the Scheduler schedules into a DailyPlan consisting of ScheduledItems.

The Scheduler's main responsibility is generating a plan.

The Owner keeps track of their name, preferences, time availabilities, and their pets.

Each Pet has a name, species, age, and notes, as well as a list of tasks that should be scheduled.

A Task has an ID, title, category, duration, priority, preferred time, and completion status.

A ScheduledItem is a Task assigned for a pet at a particulat start and end time.

The DailyPlan is a list of ScheduledItems for a particular date, and includes a list of skipped tasks if there are conflicts. It can summarize and explain choices made by the Scheduler in its creation.

**b. Design changes**

*Missing relationships*

- Task has no link back to its Pet. Owner.get_all_tasks() returns a flat list[Task], so the pet is lost. Scheduler needs the pet to build a ScheduledItem. The fix is to make get_all_tasks() return (Pet, Task) pairs, or give Task a pet_id.
- ScheduledItem and Task are linked only by object reference. If a task is edited or removed after a plan is generated, the plan shows stale data. Either treat plans as snapshots, or store the task id and look it up.
- Owner and Scheduler are not tied to a plan. Nothing stores the current plan, so Streamlit's rerun-on-every-interaction model would regenerate it each time. The UI needs to keep the Owner and the plan in st.session_state.
- Owner preferences are an untyped dict. Nothing says which keys the Scheduler reads, such as day start time, quiet hours or preferred times by category. A small Preferences dataclass would make that explicit.
- The UML says Owner has 1..* pets, but the dataclass allows zero. One of them should change.

*Logic bottlenecks*

- Time is stored as strings. start_time, end_time and preferred_time are str, which makes overlap checks and sorting error-prone. Use datetime.time or minutes since midnight.
- available_minutes is only a total. There is no day start or end, so the scheduler can't assign real clock times or honor "morning" and "evening" preferences. It needs a time window.
- Priority and time constraints can conflict. A greedy highest-priority-first pass can leave a large gap while skipping a task that would have fit. A short low-priority task may fit where a long high-priority one doesn't. The tie-breaking rule needs deciding up front, such as priority, then preferred time, then shortest first.
- Recurring tasks aren't modeled. Daily feeding and weekly grooming would have to be re-entered every day. Task.completed is also a single boolean, so it can't track completion per day.
- There are no validation rules. Nothing stops a zero or negative duration, a single task longer than the whole day, or duplicate tasks.
- Two pets' tasks can overlap. The owner can only do one thing at a time, so the schedule must be sequential across pets. This should be an explicit rule in Scheduler.
- edit_task and remove_task do linear searches by id. That's fine at this size. A dict keyed by id would only matter if the data grew.

*Suggested changes*

- Return (Pet, Task) pairs from Owner.get_all_tasks().
- Use minutes-since-midnight ints or time objects instead of time strings.
- Add day_start and day_end to Owner.
- Add a Preferences dataclass.
- Add frequency to Task for recurring tasks.
- Add validation in Task.__post_init__.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

I used AI tools for all parts of the project, including brainstorming, creating a UML diagram, programming a skeleton of the logic, and fleshing out that skeleton.

Giving the AI concrete instructions with reminders about specific requirements yielded good results.

**b. Judgment and verification**

I did not reject any AI suggestion so far. Anything I thought I would do differently, I was curious how the AI would handle it. The AI adjusted and corrected its own plan as needed while implementing the functionality.

I read and understood the AI's generated code, and tested it by running it through Python myself.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
