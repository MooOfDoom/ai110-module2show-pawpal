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

    buddy.add_task(Task("Morning walk", "exercise", 30, Priority.HIGH, preferred_start=7 * 60 + 30,
                        frequency=Frequency.DAILY))
    buddy.add_task(Task("Brush coat", "grooming", 20, Priority.LOW, preferred_start=18 * 60))
    whiskers.add_task(Task("Breakfast", "feeding", 10, Priority.HIGH, preferred_start=8 * 60,
                           frequency=Frequency.DAILY))
    whiskers.add_task(Task("Give medication", "meds", 5, Priority.HIGH, preferred_start=9 * 60))
    whiskers.add_task(Task("Laser pointer play", "enrichment", 25, Priority.MEDIUM,
                           preferred_start=17 * 60))

    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan(date.today())

    print("=" * 50)
    print(f"Today's Schedule for {owner.name} ({format_time(owner.day_start)}-"
          f"{format_time(owner.day_end)})")
    print("=" * 50)
    print(plan.explain())


if __name__ == "__main__":
    main()
