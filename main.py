"""Temporary testing ground: verify the PawPal+ logic from the terminal."""

from datetime import date

from pawpal_system import (
    Frequency,
    Owner,
    Pet,
    Preferences,
    Priority,
    Scheduler,
    Task,
    format_time,
)


def main() -> None:
    owner = Owner(
        name="Jordan",
        day_start=7 * 60,
        day_end=21 * 60,
        preferences=Preferences(quiet_hours=[(12 * 60, 13 * 60)]),  # lunch break
    )

    buddy = Pet(name="Buddy", species="dog", age=4)
    whiskers = Pet(name="Whiskers", species="cat", age=7)
    owner.add_pet(buddy)
    owner.add_pet(whiskers)

    # Tasks are deliberately added out of time order.
    whiskers.add_task(Task("Laser pointer play", "enrichment", 25, Priority.MEDIUM,
                           preferred_start=17 * 60))
    buddy.add_task(Task("Brush coat", "grooming", 20, Priority.LOW, preferred_start=18 * 60))
    whiskers.add_task(Task("Give medication", "meds", 5, Priority.HIGH, preferred_start=9 * 60))
    buddy.add_task(Task("Feed dinner", "feeding", 10, Priority.MEDIUM))  # no preferred time
    buddy.add_task(Task("Morning walk", "exercise", 30, Priority.HIGH, preferred_start=7 * 60 + 30,
                        frequency=Frequency.DAILY))
    whiskers.add_task(Task("Breakfast", "feeding", 10, Priority.HIGH, preferred_start=8 * 60,
                           frequency=Frequency.DAILY))

    # Two deliberate clashes: same pet at 07:40 (during the walk), different pets at 17:10.
    buddy.add_task(Task("Vet call", "health", 15, Priority.MEDIUM, preferred_start=7 * 60 + 40))
    buddy.add_task(Task("Training", "exercise", 20, Priority.LOW, preferred_start=17 * 60 + 10))

    scheduler = Scheduler(owner)
    today = date.today()

    # Mark a couple of tasks done so the status filter has something to show.
    for pet, task in list(owner.get_all_tasks()):
        if task.title in ("Breakfast", "Give medication"):
            pet.complete_task(task.id, today)

    def show(heading: str, pairs) -> None:
        print(f"\n{heading}")
        for pet, task in pairs:
            when = format_time(task.preferred_start) if task.preferred_start is not None else "--:--"
            status = "done" if task.is_completed(today) else "pending"
            print(f"  {when}  {pet.name:<9} {task.title:<20} [{status}]")

    show("As added (unsorted):", owner.get_all_tasks())
    show("Sorted by time:", scheduler.sort_tasks_by_time(owner.get_all_tasks()))
    show("Pet = Buddy:", scheduler.filter_tasks(pet_name="buddy"))
    show("Completed only:", scheduler.filter_tasks(completed=True))
    show("Pending only:", scheduler.filter_tasks(completed=False))
    show("Whiskers, pending, sorted by time:",
         scheduler.sort_tasks_by_time(scheduler.filter_tasks(pet_name="Whiskers", completed=False)))
    print()

    print("Conflict check:")
    conflicts = scheduler.detect_conflicts(today)
    for warning in conflicts or ["No conflicts found."]:
        print(f"  WARNING: {warning}" if conflicts else f"  {warning}")
    print()

    plan = scheduler.generate_plan(today)

    print("=" * 50)
    print(f"Today's Schedule for {owner.name} ({format_time(owner.day_start)}-"
          f"{format_time(owner.day_end)})")
    print("=" * 50)
    print(plan.explain())


if __name__ == "__main__":
    main()
