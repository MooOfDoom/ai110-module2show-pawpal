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

The scheduler considers these constraints:

- **Time:** the owner's day window (`day_start` to `day_end`), each task's duration, and the fact that the owner does one thing at a time, so tasks never overlap across pets.
- **Due date and completion:** only tasks that are due that day and not yet completed are planned. Weekly tasks appear only on their weekday, and a completed daily task returns on its next due date.
- **Priority:** high, medium or low.
- **Preferences:** a task's preferred start time, per-category time windows (for example, walks only between certain hours), and quiet hours when nothing may be scheduled.

I ranked them as hard limits first, then priority, then preferences. The day window, quiet hours, category windows and not double-booking the owner are hard: no task is ever placed in violation of them, and a task that cannot fit is skipped with a reason. Priority comes next, because it decides who gets a contested slot. Preferred start times come last, as a soft preference. If the preferred time is taken, the task moves to the next free slot, and the plan says its preferred time was unavailable.

I chose this order by asking what the owner would regret most. A missed medication or feeding costs far more than a walk at 08:00 instead of 07:30. So priority beats timing, and the tie-breakers (preferred time, then shortest duration) only matter between tasks of equal priority. Shortest-first also leaves room for more tasks in the day. Making the hard limits non-negotiable keeps the plan something the owner can actually follow.

**b. Tradeoffs**

The scheduler treats a preferred start time as a soft preference, and it places tasks greedily. It ranks tasks by priority, then preferred time, then shortest duration. Each task goes into the earliest free slot at or after its preferred start, and only falls back to the start of the day if nothing fits later. When two tasks want the same time, the higher-priority one keeps it. The lower-priority one is moved to the next gap, and `detect_conflicts` only warns about the clash instead of stopping or rearranging the plan. For example, Training (17:10, low priority) overlapped Laser pointer play (17:00-17:25), so it was moved to 17:25.

The cost is that this is not an optimal schedule. Placing a high-priority task first can push a lower-priority task away from its preferred time. It can also leave a small gap that a different ordering would have filled. The scheduler never backtracks to try another arrangement, and the conflict check only compares preferred times, not the final plan.

This is reasonable for a single owner's daily pet care. There are only a handful of tasks, and the owner does one thing at a time. Priority matters more than exact timing, since a medication should not lose its slot to grooming. A greedy pass is also easy to explain: every item in the plan has a `reason` saying why it got its time. A search for the best arrangement could produce a tighter plan, but it would be harder to explain and would be more than this app needs. Warning instead of failing keeps the app usable when the owner enters clashing times, and the plan still shows what changed.

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

The AI wrote 33 tests in `tests/test_pawpal.py`. They cover:

- **Sorting:** chronological order, untimed tasks last, ties keep their input order, and a task at 00:00 sorts first and isn't treated as untimed.
- **Filtering:** by pet (case-insensitive, blank means no filter), by completion status, and both combined.
- **Recurrence:** completing a daily or weekly task creates the next occurrence due +1 or +7 days, including month, year and leap-day rollovers. Completing twice creates no duplicate, an unknown id raises `KeyError`, and a completed recurring task is skipped until its next due date.
- **Conflict detection:** same-time clashes for the same pet and across pets, partial and one-minute overlaps, a long task flagged against every task it covers, three tasks at the same minute, back-to-back tasks (no conflict), completed tasks (ignored), and a task running past midnight.
- **Edge cases and validation:** an owner with no pets, a pet with no tasks, a task longer than the day window (skipped with a reason), bad durations and start times, a weekly task with no weekday, and duplicate pet or task names.

These mattered because they are the places where a scheduler fails quietly. A wrong date rollover or an off-by-one overlap check produces a plan that looks fine and is wrong, and the owner would only find out when a task is missed. Recurrence and conflict logic also have many boundaries (exact touch versus overlap, midnight, month ends), so I tested each boundary on purpose.

**b. Confidence**

I'm confident in the helper behaviors (sorting, filtering, recurrence, conflict detection), since each has boundary tests and all 33 pass. I'm less sure about `generate_plan` itself. The tests only check that it reports conflicts without crashing and that over-long tasks are skipped. They don't assert the ranking order or exact slot placement. I trust it from running `main.py` and reading the output, such as Training moving from 17:10 to 17:25, but that is manual checking, not a regression test. I also checked the Streamlit add, edit and remove flow with a scripted run, not a saved test.

With more time I would test:

- **Plan placement:** high priority beats low priority for a contested slot, and a short task fills a gap left by a pushed-back task.
- **Preferences:** quiet hours and category windows, since no test uses them yet.
- **Task edits:** `edit_task` and `remove_task`, including an edit that fails validation leaving the task unchanged, and an edit that renames a task to a duplicate (currently accepted).
- **Stale plans:** a plan generated before an edit still holds the old task object.
- **Time boundaries:** a task that ends exactly at `day_end`, or a day window that starts at midnight.
- **Weekly tasks:** a weekly task generated on a different weekday than the one it was created on.

---

## 5. Reflection

**a. What went well**

Everything worked pretty much first try. The specifications were clear enough that the AI could plan a successful app, and the plan of attack through creating the UML diagram and the skeleton, and integrating it with the streamlit UI resulted in a decent final product with lots of tests for verification.

**b. What you would improve**

The edit and remove UI could use some cleanup.

**c. Key takeaway**

It's important to be critical, but also useful to be flexible and curious. The AI will sometimes self-correct earlier mistakes.
