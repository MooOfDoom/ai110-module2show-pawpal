import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pawpal_system import Pet, Task


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
