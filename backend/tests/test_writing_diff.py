import pytest
import re
import json
import os
from app.schemas.writing_correction import (
    InlineEdit,
    SentenceCorrection,
    ErrorCategory,
    IELTSCriteria,
    WritingCorrectionSchema,
    WritingDiffResponse
)
from app.services.writing_diff_engine import writing_diff_engine

def test_apply_edits_to_sentence():
    sentence = "In today's connected world, air transport has become a major part of modern life, allowing people come to remote places more easily."
    edits = [
        InlineEdit(
            original="air transport",
            replacement="air travel",
            category=ErrorCategory.COLLOCATION,
            criteria=IELTSCriteria.LR,
            explanation_vi="Dùng 'air travel' chuẩn học thuật hơn."
        ),
        InlineEdit(
            original="come",
            replacement="to travel",
            category=ErrorCategory.GRAMMAR,
            criteria=IELTSCriteria.GRA,
            explanation_vi="Cấu trúc allow someone to V."
        )
    ]

    html_diff, md_diff, clean = writing_diff_engine.apply_edits_to_sentence(sentence, edits)

    # Kiểm tra HTML diff
    assert "ielts-diff-del" in html_diff
    assert "air transport" in html_diff
    assert "ielts-diff-ins" in html_diff
    assert "air travel" in html_diff
    assert "to travel" in html_diff

    # Kiểm tra Markdown diff
    assert "🔴 ~~air transport~~ ➜ 🟢 **air travel**" in md_diff
    assert "🔴 ~~come~~ ➜ 🟢 **to travel**" in md_diff

    # Kiểm tra clean text
    assert "air travel has become" in clean
    assert "allowing people to travel to remote places" in clean
    assert "air transport" not in clean
    assert "people come" not in clean
    assert re.search(r"\bcome\b", clean) is None

def test_extract_flashcards():
    sentences = [
        SentenceCorrection(
            sentence_index=1,
            original_sentence="The low cost of ticket help many people.",
            corrected_sentence="The low cost of tickets helps many people.",
            edits=[
                InlineEdit(
                    original="ticket help",
                    replacement="tickets helps",
                    category=ErrorCategory.GRAMMAR,
                    criteria=IELTSCriteria.GRA,
                    explanation_vi="Hòa hợp chủ vị và số nhiều."
                )
            ]
        )
    ]

    flashcards = writing_diff_engine.extract_flashcard_candidates(sentences)
    assert len(flashcards) == 1
    assert flashcards[0]["word"] == "tickets helps"
    assert "ticket help ❌" in flashcards[0]["front"]
    assert "tickets helps" in flashcards[0]["back"]

def test_full_essay_fixture():
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "sample_essay.json")
    with open(fixture_path, "r", encoding="utf-8") as f:
        fixture = json.load(f)

    assert "raw_essay" in fixture
    assert fixture["task_num"] == 2
    assert len(fixture["expected_edits_sample"]) >= 3
