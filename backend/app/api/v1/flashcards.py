import os
import glob
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from app.core.database import get_session
from app.core.config import settings
from app.models.flashcard import Flashcard, ReviewLog
from app.services.fsrs_engine import fsrs_service
from app.services.markdown_parser import markdown_parser

router = APIRouter(prefix="/flashcards", tags=["FSRS Flashcards"])

@router.get("/due", response_model=List[Dict[str, Any]])
def get_due_flashcards(
    limit: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_session)
):
    """Lấy danh sách thẻ đến hạn ôn tập hôm nay"""
    now = datetime.now(timezone.utc)
    statement = select(Flashcard).where(Flashcard.due <= now).order_by(Flashcard.due).limit(limit)
    cards = session.exec(statement).all()

    results = []
    for card in cards:
        preview = fsrs_service.get_preview_intervals(card)
        results.append({
            "id": str(card.id),
            "front": card.front,
            "back": card.back,
            "ipa": card.ipa,
            "part_of_speech": card.part_of_speech,
            "synonyms": card.synonyms,
            "tags": card.tags,
            "stability": card.stability,
            "difficulty": card.difficulty,
            "state": card.state,
            "reps": card.reps,
            "due": card.due.isoformat(),
            "preview_intervals": preview
        })
    return results

@router.get("/all", response_model=List[Dict[str, Any]])
def get_all_flashcards(
    tag: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = 0,
    session: Session = Depends(get_session)
):
    """Lấy toàn bộ thẻ trong kho từ vựng"""
    statement = select(Flashcard)
    if tag:
        statement = statement.where(Flashcard.tags.contains(tag))
    cards = session.exec(statement.offset(offset).limit(limit)).all()
    return [{
        "id": str(c.id),
        "front": c.front,
        "back": c.back,
        "ipa": c.ipa,
        "part_of_speech": c.part_of_speech,
        "synonyms": c.synonyms,
        "tags": c.tags,
        "state": c.state,
        "due": c.due.isoformat()
    } for c in cards]

@router.post("/{card_id}/review")
def review_flashcard(
    card_id: uuid.UUID,
    rating: int = Query(..., ge=1, le=4, description="1: Again, 2: Hard, 3: Good, 4: Easy"),
    session: Session = Depends(get_session)
):
    """Thực hiện đánh giá thẻ và cập nhật thuật toán FSRS v4"""
    card = session.get(Flashcard, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Không tìm thấy thẻ Flashcard")

    updated_card, review_log = fsrs_service.review_card(card, rating)
    session.add(updated_card)
    session.add(review_log)
    session.commit()
    session.refresh(updated_card)

    return {
        "status": "success",
        "card_id": str(updated_card.id),
        "new_due": updated_card.due.isoformat(),
        "stability": updated_card.stability,
        "difficulty": updated_card.difficulty,
        "state": updated_card.state,
        "reps": updated_card.reps,
        "scheduled_days": review_log.scheduled_days
    }

@router.post("/sync-markdown")
def sync_flashcards_from_markdown(session: Session = Depends(get_session)):
    """Quét toàn bộ thư mục content/ để trích xuất từ vựng và đồng bộ vào PostgreSQL"""
    content_dir = settings.CONTENT_DIR
    vocab_pattern = os.path.join(content_dir, "**", "vocab-*.md")
    vocab_files = glob.glob(vocab_pattern, recursive=True)

    total_added = 0
    total_updated = 0

    for file_path in vocab_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            rel_file = os.path.relpath(file_path, content_dir)
            cards_data = markdown_parser.extract_vocab_from_markdown(content, rel_file)

            for item in cards_data:
                front_word = item["front"]
                # Kiểm tra thẻ đã tồn tại chưa
                existing = session.exec(select(Flashcard).where(Flashcard.front == front_word)).first()
                if existing:
                    existing.back = item["back"]
                    existing.ipa = item.get("ipa")
                    existing.part_of_speech = item.get("part_of_speech")
                    existing.synonyms = item.get("synonyms")
                    existing.tags = item.get("tags", existing.tags)
                    session.add(existing)
                    total_updated += 1
                else:
                    new_card = Flashcard(
                        front=front_word,
                        back=item["back"],
                        ipa=item.get("ipa"),
                        part_of_speech=item.get("part_of_speech"),
                        synonyms=item.get("synonyms"),
                        tags=item.get("tags", "ielts"),
                        source_file=rel_file
                    )
                    session.add(new_card)
                    total_added += 1
            session.commit()
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=f"Lỗi khi sync {file_path}: {e}")

    return {
        "status": "success",
        "files_scanned": len(vocab_files),
        "cards_added": total_added,
        "cards_updated": total_updated
    }

@router.get("/stats")
def get_flashcard_statistics(session: Session = Depends(get_session)):
    """Thống kê tổng thể trạng thái ghi nhớ theo FSRS v4"""
    all_cards = session.exec(select(Flashcard)).all()
    now = datetime.now(timezone.utc)
    due_count = sum(1 for c in all_cards if c.due <= now)

    state_counts = {"New": 0, "Learning": 0, "Review": 0, "Relearning": 0}
    for c in all_cards:
        state_counts[c.state] = state_counts.get(c.state, 0) + 1

    total_reviews = session.exec(select(ReviewLog)).all()
    good_easy_reviews = sum(1 for r in total_reviews if r.rating in (3, 4))
    retention_rate = round((good_easy_reviews / len(total_reviews)) * 100, 1) if total_reviews else 100.0

    return {
        "total_cards": len(all_cards),
        "due_today": due_count,
        "states": state_counts,
        "total_reviews": len(total_reviews),
        "retention_rate": retention_rate
    }
