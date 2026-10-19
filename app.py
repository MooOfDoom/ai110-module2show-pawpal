import streamlit as st

from datetime import time

from pawpal_system import Frequency, Owner, Pet, Priority, Scheduler, Task, format_time

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Owner")
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan")
owner: Owner = st.session_state.owner

owner.name = st.text_input("Owner name", value=owner.name)

st.subheader("Add a Pet")
col1, col2 = st.columns(2)
with col1:
    pet_name = st.text_input("Pet name", value="Mochi")
with col2:
    species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Add pet"):
    try:
        owner.add_pet(Pet(name=pet_name.strip(), species=species))
        st.success(f"Added {pet_name} the {species}.")
    except ValueError as e:
        st.error(str(e))

if owner.pets:
    st.write("Pets: " + ", ".join(f"{p.name} ({p.species})" for p in owner.pets))
else:
    st.info("No pets yet. Add one above.")

st.markdown("### Tasks")

if owner.pets:
    pet_choice = st.selectbox("Pet", [p.name for p in owner.pets])

    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
        category = st.text_input("Category", value="exercise")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
    with col3:
        frequency = st.selectbox("Frequency", [f.value for f in Frequency])
        weekday = None
        if frequency == Frequency.WEEKLY.value:
            weekday = st.selectbox(
                "Weekday", range(7),
                format_func=lambda d: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][d],
            )

    use_pref = st.checkbox("Set a preferred start time")
    preferred_start = None
    if use_pref:
        t = st.time_input("Preferred start", value=time(8, 0))
        preferred_start = t.hour * 60 + t.minute

    if st.button("Add task"):
        pet = next(p for p in owner.pets if p.name == pet_choice)
        try:
            pet.add_task(
                Task(
                    title=task_title.strip(),
                    category=category.strip(),
                    duration_minutes=int(duration),
                    priority=Priority[priority.upper()],
                    preferred_start=preferred_start,
                    frequency=Frequency(frequency),
                    weekday=weekday,
                )
            )
            st.success(f"Added '{task_title}' to {pet.name}.")
        except ValueError as e:
            st.error(str(e))
else:
    st.info("Add a pet before adding tasks.")

scheduler = Scheduler(owner)
all_tasks = owner.get_all_tasks()

st.divider()
st.subheader("Your Tasks")

if "flash" in st.session_state:
    st.success(st.session_state.pop("flash"))

if not all_tasks:
    st.info("No tasks yet. Add one above.")
else:
    f1, f2, f3 = st.columns(3)
    with f1:
        pet_filter = st.selectbox("Show pet", ["All pets"] + [p.name for p in owner.pets])
    with f2:
        status_filter = st.selectbox("Status", ["All", "Pending", "Completed"])
    with f3:
        sort_choice = st.selectbox("Sort by", ["Time added", "Preferred time"])

    shown = scheduler.filter_tasks(
        pet_name=None if pet_filter == "All pets" else pet_filter,
        completed={"All": None, "Pending": False, "Completed": True}[status_filter],
    )
    if sort_choice == "Preferred time":
        shown = scheduler.sort_tasks_by_time(shown)

    if shown:
        st.caption(f"Showing {len(shown)} of {len(all_tasks)} tasks.")
        st.table(
            [
                {
                    "pet": pet.name,
                    "title": task.title,
                    "category": task.category,
                    "minutes": task.duration_minutes,
                    "priority": task.priority.name.lower(),
                    "preferred": format_time(task.preferred_start) if task.preferred_start is not None else "-",
                    "repeats": task.frequency.value,
                }
                for pet, task in shown
            ]
        )
    else:
        st.info("No tasks match these filters.")

    # Check for clashes as soon as tasks exist, not only after generating a schedule.
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        st.warning(
            f"**{len(conflicts)} time clash{'es' if len(conflicts) != 1 else ''} found.** "
            "These tasks want overlapping times. You can still generate a schedule: "
            "PawPal+ will move the lower-priority task to the next free slot."
        )
        for message in conflicts:
            st.warning(message.replace("Conflict ", "", 1).capitalize(), icon="⚠️")
        st.caption("Fix it by changing one task's preferred start time, or by shortening a task.")

    with st.expander("Edit or remove a task"):
        by_id = {task.id: (pet, task) for pet, task in all_tasks}
        task_id = st.selectbox(
            "Task",
            list(by_id),
            format_func=lambda i: f"{by_id[i][0].name} / {by_id[i][1].title}",
        )
        edit_pet, edit_task = by_id[task_id]
        k = task_id  # widget keys per task, so fields reset when the selection changes

        e1, e2, e3 = st.columns(3)
        with e1:
            new_title = st.text_input("Title", value=edit_task.title, key=f"title_{k}")
            new_category = st.text_input("Category", value=edit_task.category, key=f"cat_{k}")
        with e2:
            new_duration = st.number_input(
                "Duration (minutes)", min_value=1, max_value=240,
                value=min(edit_task.duration_minutes, 240), key=f"dur_{k}",
            )
            new_priority = st.selectbox(
                "Priority", ["low", "medium", "high"],
                index=edit_task.priority.value - 1, key=f"pri_{k}",
            )
        with e3:
            freqs = [f.value for f in Frequency]
            new_frequency = st.selectbox(
                "Frequency", freqs, index=freqs.index(edit_task.frequency.value), key=f"freq_{k}"
            )
            new_weekday = None
            if new_frequency == Frequency.WEEKLY.value:
                new_weekday = st.selectbox(
                    "Weekday", range(7), index=edit_task.weekday or 0, key=f"wd_{k}",
                    format_func=lambda d: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][d],
                )

        has_pref = st.checkbox(
            "Preferred start time", value=edit_task.preferred_start is not None, key=f"haspref_{k}"
        )
        new_start = None
        if has_pref:
            current = edit_task.preferred_start if edit_task.preferred_start is not None else 8 * 60
            t = st.time_input("Preferred start", value=time(current // 60, current % 60), key=f"start_{k}")
            new_start = t.hour * 60 + t.minute

        save_col, delete_col = st.columns(2)
        if save_col.button("Save changes", key=f"save_{k}"):
            try:
                edit_pet.edit_task(
                    task_id,
                    title=new_title.strip(),
                    category=new_category.strip(),
                    duration_minutes=int(new_duration),
                    priority=Priority[new_priority.upper()],
                    preferred_start=new_start,
                    frequency=Frequency(new_frequency),
                    weekday=new_weekday,
                )
                st.session_state.pop("plan", None)  # the old plan is now stale
                st.session_state.flash = f"Updated '{new_title.strip()}'."
                st.rerun()
            except ValueError as e:
                st.error(str(e))
        if delete_col.button("Remove task", key=f"del_{k}"):
            edit_pet.remove_task(task_id)
            st.session_state.pop("plan", None)
            st.session_state.flash = f"Removed '{edit_task.title}' from {edit_pet.name}."
            st.rerun()

st.divider()

st.subheader("Build Schedule")
st.caption(f"Plans the day from {format_time(owner.day_start)} to {format_time(owner.day_end)}.")

if st.button("Generate schedule", type="primary"):
    if not all_tasks:
        st.warning("Add at least one task first.")
    else:
        st.session_state.plan = scheduler.generate_plan()

plan = st.session_state.get("plan")
if plan:
    if plan.items and not plan.skipped:
        st.success(f"All {len(plan.items)} tasks fit today ({plan.total_minutes} min scheduled).")
    elif plan.items:
        st.warning(
            f"Scheduled {len(plan.items)} tasks ({plan.total_minutes} min), "
            f"but {len(plan.skipped)} did not fit."
        )
    else:
        st.error("Nothing could be scheduled today.")

    for w in plan.warnings:
        st.warning(w, icon="⚠️")

    if plan.items:
        st.markdown("#### Today's plan")
        st.table(
            [
                {
                    "time": f"{format_time(i.start_time)}-{format_time(i.end_time)}",
                    "pet": i.pet.name,
                    "task": i.task.title,
                    "priority": i.task.priority.name.lower(),
                    "why": i.reason,
                }
                for i in plan.items
            ]
        )
    if plan.skipped:
        st.markdown("#### Could not schedule")
        for pet, task, why in plan.skipped:
            st.error(f"**{pet.name} / {task.title}**: {why}")
