import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pawpal_system import Frequency, Owner, Pet, Scheduler, Task


def test_mark_complete_changes_task_status():
    today = date.today()
    task = Task("Morning walk", "exercise", 30)

    assert not task.is_completed(today)

    task.mark_complete(today)

    assert task.is_completed(today)


def test_adding_task_increases_pet_task_count():
    pet = Pet("Buddy", "dog")
    assert len(pet.tasks) == 0

    pet.add_task(Task("Morning walk", "exercise", 30))

    assert len(pet.tasks) == 1


def make_scheduler():
    """Owner with two pets whose tasks are added out of time order."""
    owner = Owner("Jordan")
    buddy, whiskers = Pet("Buddy", "dog"), Pet("Whiskers", "cat")
    owner.add_pet(buddy)
    owner.add_pet(whiskers)
    whiskers.add_task(Task("Play", "enrichment", 25, preferred_start=17 * 60))
    buddy.add_task(Task("Feed", "feeding", 10))  # no preferred time
    buddy.add_task(Task("Walk", "exercise", 30, preferred_start=7 * 60 + 30))
    whiskers.add_task(Task("Meds", "meds", 5, preferred_start=9 * 60))
    return Scheduler(owner)


def test_sort_tasks_by_time_orders_chronologically_with_untimed_last():
    scheduler = make_scheduler()

    result = scheduler.sort_tasks_by_time(scheduler.owner.get_all_tasks())

    assert [t.title for _, t in result] == ["Walk", "Meds", "Play", "Feed"]


def test_filter_tasks_by_pet_name_is_case_insensitive():
    scheduler = make_scheduler()

    result = scheduler.filter_tasks(pet_name=" buddy ")

    assert {t.title for _, t in result} == {"Feed", "Walk"}
    assert all(pet.name == "Buddy" for pet, _ in result)


def test_filter_tasks_by_completion_status():
    scheduler = make_scheduler()
    today = date.today()
    for _, task in scheduler.owner.get_all_tasks():
        if task.title == "Meds":
            task.mark_complete(today)

    done = scheduler.filter_tasks(completed=True, day=today)
    pending = scheduler.filter_tasks(completed=False, day=today)

    assert [t.title for _, t in done] == ["Meds"]
    assert {t.title for _, t in pending} == {"Play", "Feed", "Walk"}


def test_filter_tasks_combines_pet_and_status_and_no_filter_returns_all():
    scheduler = make_scheduler()

    assert len(scheduler.filter_tasks()) == 4
    assert [t.title for _, t in scheduler.filter_tasks("Whiskers", completed=False)] == [
        "Play",
        "Meds",
    ]
    assert scheduler.filter_tasks(pet_name="Nobody") == []


def test_completing_daily_task_creates_instance_due_tomorrow():
    pet = Pet("Buddy", "dog")
    walk = Task("Walk", "exercise", 30, frequency=Frequency.DAILY)
    pet.add_task(walk)
    today = date.today()

    nxt = pet.complete_task(walk.id, today)

    assert nxt is not None and nxt.id != walk.id
    assert nxt.due_date == today + timedelta(days=1)
    assert not nxt.is_completed(today)
    assert len(pet.tasks) == 2
    assert not nxt.is_due(today) and nxt.is_due(today + timedelta(days=1))


def test_completing_weekly_task_creates_instance_due_in_seven_days():
    pet = Pet("Whiskers", "cat")
    today = date.today()
    bath = Task("Bath", "grooming", 20, frequency=Frequency.WEEKLY, weekday=today.weekday())
    pet.add_task(bath)

    nxt = pet.complete_task(bath.id, today)

    assert nxt.due_date == today + timedelta(days=7)
    assert nxt.weekday == today.weekday()


def test_daily_recurrence_rolls_over_month_and_year_end():
    task = Task("Feed", "feeding", 10, frequency=Frequency.DAILY)

    nxt = task.mark_complete(date(2026, 12, 31))

    assert nxt.due_date == date(2027, 1, 1)


def test_once_task_and_repeat_completion_create_no_new_instance():
    pet = Pet("Buddy", "dog")
    once = Task("Vet visit", "health", 60)
    daily = Task("Walk", "exercise", 30, frequency=Frequency.DAILY)
    pet.add_task(once)
    pet.add_task(daily)
    today = date.today()

    assert pet.complete_task(once.id, today) is None
    assert pet.complete_task(daily.id, today) is not None
    assert pet.complete_task(daily.id, today) is None  # already done: no duplicate
    assert len(pet.tasks) == 3


def test_scheduler_skips_completed_recurring_task_until_next_due_date():
    owner = Owner("Jordan")
    pet = Pet("Buddy", "dog")
    owner.add_pet(pet)
    walk = Task("Walk", "exercise", 30, frequency=Frequency.DAILY)
    pet.add_task(walk)
    today = date.today()
    pet.complete_task(walk.id, today)
    scheduler = Scheduler(owner)

    assert scheduler.generate_plan(today).items == []
    assert len(scheduler.generate_plan(today + timedelta(days=1)).items) == 1


def conflict_scheduler(*specs):
    """Scheduler where each spec is (pet_name, title, start_minute, duration)."""
    owner = Owner("Jordan")
    pets = {}
    for pet_name, title, start, duration in specs:
        if pet_name not in pets:
            pets[pet_name] = Pet(pet_name, "dog")
            owner.add_pet(pets[pet_name])
        pets[pet_name].add_task(Task(title, "misc", duration, preferred_start=start))
    return Scheduler(owner)


def test_detects_same_time_conflict_across_pets():
    scheduler = conflict_scheduler(("Buddy", "Walk", 540, 30), ("Whiskers", "Meds", 540, 5))

    warnings = scheduler.detect_conflicts(date.today())

    assert len(warnings) == 1
    assert "across pets" in warnings[0] and "Walk" in warnings[0] and "Meds" in warnings[0]


def test_detects_overlap_for_same_pet():
    scheduler = conflict_scheduler(("Buddy", "Walk", 540, 30), ("Buddy", "Brush", 560, 10))

    warnings = scheduler.detect_conflicts(date.today())

    assert len(warnings) == 1 and "same pet" in warnings[0]


def test_back_to_back_and_untimed_tasks_do_not_conflict():
    scheduler = conflict_scheduler(("Buddy", "Walk", 540, 30), ("Buddy", "Brush", 570, 10))
    scheduler.owner.pets[0].add_task(Task("Feed", "feeding", 10))  # no preferred time

    assert scheduler.detect_conflicts(date.today()) == []


def test_long_task_conflicts_with_every_task_it_covers():
    scheduler = conflict_scheduler(
        ("Buddy", "Hike", 540, 120), ("Buddy", "Water", 560, 5), ("Buddy", "Snack", 600, 5)
    )

    assert len(scheduler.detect_conflicts(date.today())) == 2


def test_generate_plan_reports_conflicts_without_crashing():
    scheduler = conflict_scheduler(("Buddy", "Walk", 540, 30), ("Whiskers", "Meds", 540, 5))

    plan = scheduler.generate_plan(date.today())

    assert len(plan.warnings) == 1
    assert len(plan.items) == 2  # both still scheduled, the second at a free slot
    assert "Warnings:" in plan.explain()
