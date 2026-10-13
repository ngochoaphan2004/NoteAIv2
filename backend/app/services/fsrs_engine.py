from datetime import datetime, timezone, timedelta
from typing import Dict, Tuple, Optional
from fsrs import Scheduler, Card as FSRSCard, Rating, State
from app.models.flashcard import Flashcard, ReviewLog

class FSRSService:
    def __init__(self):
        # Khởi tạo scheduler chuẩn FSRS
        self.scheduler = Scheduler()

    def _to_fsrs_card(self, db_card: Flashcard) -> FSRSCard:
        """Chuyển đổi từ DB model Flashcard sang thực thể toán học FSRS Card"""
        fsrs_card = FSRSCard()
        if db_card.stability > 0:
            fsrs_card.stability = db_card.stability
        if db_card.difficulty > 0:
            fsrs_card.difficulty = db_card.difficulty
        
        # Đảm bảo datetime có timezone UTC
        if db_card.due:
            if db_card.due.tzinfo is None:
                fsrs_card.due = db_card.due.replace(tzinfo=timezone.utc)
            else:
                fsrs_card.due = db_card.due

        if db_card.last_review:
            if db_card.last_review.tzinfo is None:
                fsrs_card.last_review = db_card.last_review.replace(tzinfo=timezone.utc)
            else:
                fsrs_card.last_review = db_card.last_review

        # Map state string sang FSRS State enum
        state_map = {
            "Learning": State.Learning,
            "Review": State.Review,
            "Relearning": State.Relearning
        }
        if db_card.state in state_map:
            fsrs_card.state = state_map[db_card.state]
        return fsrs_card

    def review_card(self, db_card: Flashcard, rating_val: int) -> Tuple[Flashcard, ReviewLog]:
        """
        Thực hiện đánh giá thẻ và cập nhật các tham số DSR (Difficulty, Stability, Retrievability)
        rating_val: 1 (Again), 2 (Hard), 3 (Good), 4 (Easy)
        """
        fsrs_card = self._to_fsrs_card(db_card)
        rating_enum = Rating(rating_val)
        now = datetime.now(timezone.utc)

        # Tính toán lịch lặp tiếp theo bằng công thức DSR
        updated_fsrs_card, fsrs_log = self.scheduler.review_card(fsrs_card, rating_enum, now)

        # Tính khoảng cách ngày
        delta_seconds = max(0.0, (updated_fsrs_card.due - now).total_seconds())
        scheduled_days = round(delta_seconds / 86400, 4)

        elapsed_days = 0.0
        if db_card.last_review:
            last_dt = db_card.last_review.replace(tzinfo=timezone.utc) if db_card.last_review.tzinfo is None else db_card.last_review
            elapsed_days = round(max(0.0, (now - last_dt).total_seconds()) / 86400, 4)

        # Cập nhật ngược lại Flashcard database model
        db_card.stability = round(float(updated_fsrs_card.stability), 4) if updated_fsrs_card.stability else 0.0
        db_card.difficulty = round(float(updated_fsrs_card.difficulty), 4) if updated_fsrs_card.difficulty else 0.0
        db_card.reps += 1
        if rating_val == 1:
            db_card.lapses += 1
        db_card.due = updated_fsrs_card.due
        db_card.last_review = now
        db_card.state = updated_fsrs_card.state.name

        # Tạo bản ghi log ôn tập
        log = ReviewLog(
            card_id=db_card.id,
            rating=rating_val,
            scheduled_days=scheduled_days,
            elapsed_days=elapsed_days,
            review_state=updated_fsrs_card.state.name,
            review_time=now
        )
        return db_card, log

    def get_preview_intervals(self, db_card: Flashcard) -> Dict[str, str]:
        """Tính toán khoảng cách ngày xem trước (preview intervals) cho cả 4 nút UI"""
        now = datetime.now(timezone.utc)
        result = {}
        rating_map = {
            Rating.Again: "again",
            Rating.Hard: "hard",
            Rating.Good: "good",
            Rating.Easy: "easy"
        }

        for rating_enum, key in rating_map.items():
            fsrs_card = self._to_fsrs_card(db_card)
            try:
                card_after, _ = self.scheduler.review_card(fsrs_card, rating_enum, now)
                delta = card_after.due - now
                result[key] = self._format_timedelta(delta)
            except Exception:
                result[key] = "1d"

        return result

    @staticmethod
    def _format_timedelta(delta: timedelta) -> str:
        """Định dạng thời gian thân thiện cho UI (ví dụ: 10m, 1d, 4d, 1.2m)"""
        total_seconds = int(delta.total_seconds())
        if total_seconds < 60:
            return "1m"
        elif total_seconds < 3600:
            return f"{max(1, total_seconds // 60)}m"
        elif total_seconds < 86400:
            return f"{total_seconds // 3600}h"
        else:
            days = total_seconds / 86400
            if days < 30:
                return f"{int(round(days))}d"
            elif days < 365:
                return f"{round(days / 30, 1)}m"
            else:
                return f"{round(days / 365, 1)}y"

fsrs_service = FSRSService()
