import uuid
from datetime import datetime, timezone
import pytest
from app.models.flashcard import Flashcard
from app.services.fsrs_engine import fsrs_service

def test_fsrs_review_good():
    card = Flashcard(
        id=uuid.uuid4(),
        front="uphill",
        back="Lên dốc, gian nan",
        stability=0.0,
        difficulty=0.0,
        due=datetime.now(timezone.utc),
        reps=0,
        lapses=0,
        state="New"
    )

    # Đánh giá Good (3)
    updated_card, log = fsrs_service.review_card(card, rating_val=3)

    assert updated_card.reps == 1
    assert updated_card.stability > 0.0
    assert updated_card.difficulty > 0.0
    assert updated_card.due > datetime.now(timezone.utc)
    assert log.rating == 3
    assert log.scheduled_days >= 0.0

def test_fsrs_review_again_lapses():
    card = Flashcard(
        id=uuid.uuid4(),
        front="vulnerable",
        back="Dễ bị tổn thương",
        stability=2.5,
        difficulty=5.0,
        due=datetime.now(timezone.utc),
        reps=3,
        lapses=0,
        state="Review"
    )

    # Đánh giá Again (1)
    updated_card, log = fsrs_service.review_card(card, rating_val=1)

    assert updated_card.lapses == 1
    assert updated_card.state in ("Relearning", "Learning")
    assert log.rating == 1

def test_fsrs_preview_intervals():
    card = Flashcard(
        id=uuid.uuid4(),
        front="mitigate",
        back="Làm dịu bớt, giảm nhẹ",
        stability=1.0,
        difficulty=4.0,
        due=datetime.now(timezone.utc),
        reps=1,
        state="Learning"
    )

    previews = fsrs_service.get_preview_intervals(card)
    assert "again" in previews
    assert "hard" in previews
    assert "good" in previews
    assert "easy" in previews
