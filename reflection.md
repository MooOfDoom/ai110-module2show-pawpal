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

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

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

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

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
