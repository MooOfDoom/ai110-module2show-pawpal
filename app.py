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

all_tasks = owner.get_all_tasks()
if all_tasks:
    st.write("Current tasks:")
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
            for pet, task in all_tasks
        ]
    )
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption(f"Plans the day from {format_time(owner.day_start)} to {format_time(owner.day_end)}.")

if st.button("Generate schedule"):
    if not all_tasks:
        st.warning("Add at least one task first.")
    else:
        st.session_state.plan = Scheduler(owner).generate_plan()

plan = st.session_state.get("plan")
if plan:
    st.markdown(f"#### Today's plan ({plan.total_minutes} min scheduled)")
    if plan.items:
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
    for pet, task, why in plan.skipped:
        st.warning(f"Skipped {pet.name} / {task.title}: {why}")
