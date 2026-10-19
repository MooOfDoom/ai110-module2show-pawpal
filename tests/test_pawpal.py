import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

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


# ---------------------------------------------------------------- edge cases


def test_empty_owner_and_pet_without_tasks_produce_empty_results():
    owner = Owner("Jordan")
    scheduler = Scheduler(owner)

    assert scheduler.sort_tasks_by_time([]) == []
    assert scheduler.filter_tasks() == []
    assert scheduler.detect_conflicts(date.today()) == []
    assert scheduler.generate_plan(date.today()).items == []

    owner.add_pet(Pet("Buddy", "dog"))  # a pet with no tasks
    plan = scheduler.generate_plan(date.today())

    assert owner.get_all_tasks() == []
    assert plan.items == [] and plan.skipped == [] and plan.warnings == []
    assert "nothing scheduled" in plan.explain()


def test_midnight_preferred_start_sorts_first_not_as_untimed():
    pet = Pet("Buddy", "dog")
    pet.add_task(Task("Feed", "feeding", 10))
    pet.add_task(Task("Late", "misc", 10, preferred_start=600))
    pet.add_task(Task("Midnight", "misc", 10, preferred_start=0))
    owner = Owner("Jordan")
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    result = scheduler.sort_tasks_by_time(owner.get_all_tasks())

    assert [t.title for _, t in result] == ["Midnight", "Late", "Feed"]


def test_sort_is_stable_for_equal_times_and_for_untimed_tasks():
    pet = Pet("Buddy", "dog")
    for title, start in [("B", 540), ("A", 540), ("Y", None), ("X", None), ("C", 540)]:
        pet.add_task(Task(title, title, 10, preferred_start=start))
    owner = Owner("Jordan")
    owner.add_pet(pet)

    result = Scheduler(owner).sort_tasks_by_time(owner.get_all_tasks())

    assert [t.title for _, t in result] == ["B", "A", "C", "Y", "X"]


def test_identical_start_for_same_pet_is_a_same_pet_conflict():
    scheduler = conflict_scheduler(("Buddy", "Walk", 540, 30), ("Buddy", "Brush", 540, 30))

    warnings = scheduler.detect_conflicts(date.today())

    assert len(warnings) == 1 and "same pet" in warnings[0]


def test_three_tasks_at_same_minute_each_conflict_with_the_first():
    scheduler = conflict_scheduler(
        ("Buddy", "A", 540, 30), ("Whiskers", "B", 540, 30), ("Rex", "C", 540, 30)
    )

    assert len(scheduler.detect_conflicts(date.today())) == 2


def test_one_minute_overlap_conflicts_but_exact_touch_does_not():
    overlap = conflict_scheduler(("Buddy", "Walk", 540, 30), ("Whiskers", "Meds", 569, 5))
    touch = conflict_scheduler(("Buddy", "Walk", 540, 30), ("Whiskers", "Meds", 570, 5))

    assert len(overlap.detect_conflicts(date.today())) == 1
    assert touch.detect_conflicts(date.today()) == []


def test_completed_task_no_longer_conflicts():
    scheduler = conflict_scheduler(("Buddy", "Walk", 540, 30), ("Whiskers", "Meds", 540, 5))
    today = date.today()
    scheduler.owner.pets[1].tasks[0].mark_complete(today)

    assert scheduler.detect_conflicts(today) == []


def test_weekly_task_completed_on_other_weekday_recurs_from_completion_day():
    pet = Pet("Whiskers", "cat")
    wednesday = date(2026, 10, 21)
    bath = Task("Bath", "grooming", 20, frequency=Frequency.WEEKLY, weekday=0)  # Monday
    pet.add_task(bath)

    nxt = pet.complete_task(bath.id, wednesday)

    assert nxt.due_date == date(2026, 10, 28)
    assert nxt.weekday == wednesday.weekday()  # follows the new due date


def test_recurrence_across_leap_day():
    daily = Task("Feed", "feeding", 10, frequency=Frequency.DAILY)
    weekly = Task("Bath", "grooming", 20, frequency=Frequency.WEEKLY, weekday=1)

    assert daily.next_occurrence(date(2028, 2, 28)).due_date == date(2028, 2, 29)
    assert daily.next_occurrence(date(2028, 2, 29)).due_date == date(2028, 3, 1)
    assert daily.next_occurrence(date(2027, 2, 28)).due_date == date(2027, 3, 1)
    assert weekly.next_occurrence(date(2028, 2, 22)).due_date == date(2028, 2, 29)


def test_complete_task_with_unknown_id_raises_key_error():
    pet = Pet("Buddy", "dog")
    pet.add_task(Task("Walk", "exercise", 30))

    with pytest.raises(KeyError):
        pet.complete_task("does-not-exist", date.today())


def test_completing_a_chain_of_daily_tasks_leaves_one_pending():
    pet = Pet("Buddy", "dog")
    pet.add_task(Task("Walk", "exercise", 30, frequency=Frequency.DAILY))
    day = date(2026, 10, 18)

    for offset in range(3):
        current = day + timedelta(days=offset)
        pending = [t for t in pet.tasks if not t.is_completed(current)]
        assert len(pending) == 1
        pet.complete_task(pending[0].id, current)

    assert len(pet.tasks) == 4
    pending = [t for t in pet.tasks if not t.is_completed(day)]
    assert len(pending) == 1 and pending[0].due_date == day + timedelta(days=3)


def test_is_due_respects_due_date_and_weekly_weekday():
    day = date(2026, 10, 19)  # Monday
    future = Task("Walk", "exercise", 30, due_date=day + timedelta(days=1))
    past = Task("Walk", "exercise", 30, due_date=day - timedelta(days=5))
    weekly_mon = Task("Bath", "grooming", 20, frequency=Frequency.WEEKLY, weekday=0)
    weekly_tue = Task("Bath", "grooming", 20, frequency=Frequency.WEEKLY, weekday=1)

    assert not future.is_due(day) and future.is_due(day + timedelta(days=1))
    assert past.is_due(day)
    assert weekly_mon.is_due(day) and not weekly_tue.is_due(day)


def test_task_validation_rejects_bad_duration_start_and_weekly_without_weekday():
    with pytest.raises(ValueError):
        Task("Zero", "misc", 0)
    with pytest.raises(ValueError):
        Task("Negative start", "misc", 10, preferred_start=-1)
    with pytest.raises(ValueError):
        Task("Past midnight start", "misc", 10, preferred_start=1440)
    with pytest.raises(ValueError):
        Task("Bath", "grooming", 20, frequency=Frequency.WEEKLY)


def test_task_running_past_midnight_conflicts_and_is_skipped_without_crashing():
    scheduler = conflict_scheduler(("Buddy", "Late walk", 1430, 30), ("Whiskers", "Meds", 1439, 5))

    assert len(scheduler.detect_conflicts(date.today())) == 1

    plan = scheduler.generate_plan(date.today())  # default day window ends at 20:00

    assert len(plan.warnings) == 1
    assert len(plan.skipped) + len(plan.items) == 2


def test_task_longer_than_day_window_is_skipped_with_reason():
    owner = Owner("Jordan", day_start=8 * 60, day_end=9 * 60)
    pet = Pet("Buddy", "dog")
    owner.add_pet(pet)
    pet.add_task(Task("Hike", "exercise", 120))

    plan = Scheduler(owner).generate_plan(date.today())

    assert plan.items == [] and len(plan.skipped) == 1
    assert "Skipped:" in plan.explain()


def test_filter_blank_pet_name_means_no_filter_and_completed_defaults_to_today():
    scheduler = make_scheduler()
    for _, task in scheduler.owner.get_all_tasks():
        if task.title == "Walk":
            task.mark_complete(date.today())

    assert len(scheduler.filter_tasks(pet_name="   ")) == 4
    assert len(scheduler.filter_tasks(pet_name="")) == 4
    assert [t.title for _, t in scheduler.filter_tasks(completed=True)] == ["Walk"]


def test_duplicate_pet_name_and_duplicate_task_are_rejected():
    owner = Owner("Jordan")
    owner.add_pet(Pet("Buddy", "dog"))
    with pytest.raises(ValueError):
        owner.add_pet(Pet(" buddy ", "cat"))

    pet = Pet("Rex", "dog")
    pet.add_task(Task("Walk", "exercise", 30))
    with pytest.raises(ValueError):
        pet.add_task(Task("walk", "Exercise", 15))
