import os
import sys
import json
import time
import argparse
from typing import List, Dict, Any
from dotenv import load_dotenv
from google import genai
from PIL import Image

# Đảm bảo UTF-8 trên Windows console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Load môi trường
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY không tìm thấy trong backend/.env")

client = genai.Client(api_key=api_key)
FALLBACK_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-3-flash-preview"
]

# Định nghĩa bảng phân trang chính xác theo Mục lục sách IZONE Cambridge 18
TEST_CONFIGS = {
    1: {
        "title": "Cambridge IELTS 18 - Test 1",
        "sections": [
            {
                "skill": "listening",
                "part": 1,
                "name": "Listening Part 1",
                "question_range": (1, 10),
                "pages": [11, 12, 13]
            },
            {
                "skill": "listening",
                "part": 2,
                "name": "Listening Part 2",
                "question_range": (11, 20),
                "pages": [14, 15, 16, 17, 18, 19]
            },
            {
                "skill": "listening",
                "part": 3,
                "name": "Listening Part 3",
                "question_range": (21, 30),
                "pages": [19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29]
            },
            {
                "skill": "listening",
                "part": 4,
                "name": "Listening Part 4",
                "question_range": (31, 40),
                "pages": [30, 31, 32, 33, 34]
            },
            {
                "skill": "reading",
                "part": 1,
                "name": "Reading Passage 1: Urban Farming",
                "question_range": (1, 13),
                "pages": [35, 36, 37, 38]
            },
            {
                "skill": "reading",
                "part": 2,
                "name": "Reading Passage 2: Forest Management in Pennsylvania, USA",
                "question_range": (14, 26),
                "pages": [39, 40, 41, 42, 43, 44]
            },
            {
                "skill": "reading",
                "part": 3,
                "name": "Reading Passage 3: Conquering Earth's Space Junk Problem",
                "question_range": (27, 40),
                "pages": [44, 45, 46, 47, 48, 49, 50]
            }
        ]
    },
    2: {
        "title": "Cambridge IELTS 18 - Test 2",
        "sections": [
            {
                "skill": "listening",
                "part": 1,
                "name": "Listening Part 1",
                "question_range": (1, 10),
                "pages": [51, 52, 53]
            },
            {
                "skill": "listening",
                "part": 2,
                "name": "Listening Part 2",
                "question_range": (11, 20),
                "pages": [54, 55, 56, 57, 58, 59]
            },
            {
                "skill": "listening",
                "part": 3,
                "name": "Listening Part 3",
                "question_range": (21, 30),
                "pages": [60, 61, 62, 63, 64, 65]
            },
            {
                "skill": "listening",
                "part": 4,
                "name": "Listening Part 4",
                "question_range": (31, 40),
                "pages": [66, 67, 68, 69]
            },
            {
                "skill": "reading",
                "part": 1,
                "name": "Reading Passage 1: Stonehenge",
                "question_range": (1, 13),
                "pages": [70, 71, 72, 73, 74]
            },
            {
                "skill": "reading",
                "part": 2,
                "name": "Reading Passage 2: Living With Artificial Intelligence",
                "question_range": (14, 26),
                "pages": [75, 76, 77, 78, 79, 80, 81, 82, 83, 84]
            },
            {
                "skill": "reading",
                "part": 3,
                "name": "Reading Passage 3: An Ideal City",
                "question_range": (27, 40),
                "pages": [85, 86, 87, 88, 89, 90]
            }
        ]
    },
    3: {
        "title": "Cambridge IELTS 18 - Test 3",
        "sections": [
            {
                "skill": "listening",
                "part": 1,
                "name": "Listening Part 1",
                "question_range": (1, 10),
                "pages": [91, 92, 93, 94]
            },
            {
                "skill": "listening",
                "part": 2,
                "name": "Listening Part 2",
                "question_range": (11, 20),
                "pages": [94, 95, 96, 97, 98, 99, 100]
            },
            {
                "skill": "listening",
                "part": 3,
                "name": "Listening Part 3",
                "question_range": (21, 30),
                "pages": [101, 102, 103, 104, 105]
            },
            {
                "skill": "listening",
                "part": 4,
                "name": "Listening Part 4",
                "question_range": (31, 40),
                "pages": [106, 107, 108, 109]
            },
            {
                "skill": "reading",
                "part": 1,
                "name": "Reading Passage 1: Materials to Take Us Beyond Concrete",
                "question_range": (1, 13),
                "pages": [110, 111, 112, 113, 114, 115]
            },
            {
                "skill": "reading",
                "part": 2,
                "name": "Reading Passage 2: The Steam Car",
                "question_range": (14, 26),
                "pages": [115, 116, 117, 118, 119, 120, 121, 122]
            },
            {
                "skill": "reading",
                "part": 3,
                "name": "Reading Passage 3: The Case for Mixed-Ability Classes",
                "question_range": (27, 40),
                "pages": [123, 124, 125, 126, 127, 128, 129, 130, 131]
            }
        ]
    },
    4: {
        "title": "Cambridge IELTS 18 - Test 4",
        "sections": [
            {
                "skill": "listening",
                "part": 1,
                "name": "Listening Part 1",
                "question_range": (1, 10),
                "pages": [132, 133, 134, 135]
            },
            {
                "skill": "listening",
                "part": 2,
                "name": "Listening Part 2",
                "question_range": (11, 20),
                "pages": [136, 137, 138, 139, 140, 141]
            },
            {
                "skill": "listening",
                "part": 3,
                "name": "Listening Part 3",
                "question_range": (21, 30),
                "pages": [141, 142, 143, 144, 145, 146]
            },
            {
                "skill": "listening",
                "part": 4,
                "name": "Listening Part 4",
                "question_range": (31, 40),
                "pages": [147, 148, 149, 150]
            },
            {
                "skill": "reading",
                "part": 1,
                "name": "Reading Passage 1: Green Roofs",
                "question_range": (1, 13),
                "pages": [151, 152, 153, 154, 155, 156, 157, 158]
            },
            {
                "skill": "reading",
                "part": 2,
                "name": "Reading Passage 2: The Growth Mindset",
                "question_range": (14, 26),
                "pages": [159, 160, 161, 162, 163, 164, 165]
            },
            {
                "skill": "reading",
                "part": 3,
                "name": "Reading Passage 3: Alfred Wegener: Science, Exploration and Continental Drift",
                "question_range": (27, 40),
                "pages": [166, 167, 168, 169, 170, 171, 172, 173, 174]
            }
        ]
    }
}

def recover_missing_question(q_num: int, pages: List[int], images_dir: str, skill: str, part: int, name: str) -> Any:
    images = []
    for p in pages:
        img_path = os.path.join(images_dir, f"page_{p:03d}.png")
        if os.path.exists(img_path):
            images.append(Image.open(img_path))

    prompt = f"""Bạn là chuyên gia trích xuất dữ liệu khảo thí IELTS.
Nhiệm vụ: Tìm và trích xuất DUY NHẤT thông tin câu hỏi số {q_num} từ các trang sách của phần: {name}.
Yêu cầu định dạng: Trả về DUY NHẤT một JSON Object thuần túy (không bọc bất kỳ giải thích ngoài JSON):
{{
  "question_number": {q_num},
  "question_type": "Gap-fill / Multiple choice / Matching / True-False-Not Given / Yes-No-Not Given",
  "question_text": "Tóm tắt nội dung câu hỏi hoặc câu có chỗ trống số {q_num}",
  "answer": "Đáp án chính thức trong sách",
  "explanation": "Giải thích chi tiết bằng tiếng Việt vì sao chọn đáp án này, phân tích bẫy nếu có",
  "evidence": "Trích dẫn transcript hoặc câu dẫn chứng trong bài đọc",
  "keywords": ["từ", "khóa"]
}}"""

    for model_name in FALLBACK_MODELS:
        try:
            res = client.models.generate_content(
                model=model_name,
                contents=[prompt, *images]
            )
            text = res.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            q_data = json.loads(text)
            if isinstance(q_data, dict) and q_data.get("question_number") == q_num:
                q_data["skill"] = skill
                q_data["part"] = part
                print(f"      🎯 Đã bổ sung thành công câu {q_num} với model {model_name}!")
                return q_data
        except Exception as e:
            time.sleep(2)
    return None

def extract_section(section: Dict[str, Any], images_dir: str, max_retries: int = 3) -> List[Dict[str, Any]]:
    pages = section["pages"]
    q_start, q_end = section["question_range"]
    skill = section["skill"]
    part = section["part"]
    name = section["name"]

    print(f"  👉 Đang xử lý: {name} (Câu {q_start} đến {q_end}) | {len(pages)} trang ảnh...")

    # Chia thành các lô 3-4 trang để tránh tràn context và sót câu
    batch_size = 4
    page_batches = [pages[i:i + batch_size] for i in range(0, len(pages), batch_size)]

    all_questions = []

    for b_idx, batch in enumerate(page_batches):
        images = []
        for p in batch:
            img_path = os.path.join(images_dir, f"page_{p:03d}.png")
            if os.path.exists(img_path):
                images.append(Image.open(img_path))
            else:
                print(f"    ⚠️ Cảnh báo: Không tìm thấy file ảnh {img_path}")

        if not images:
            continue

        prompt = f"""Bạn là chuyên gia trích xuất dữ liệu khảo thí IELTS.
Nhiệm vụ: Trích xuất TOÀN BỘ các câu hỏi, đáp án chính thức và phần giải thích/dẫn chứng xuất hiện trong các trang sách này của phần: {name}.
Khoảng câu hỏi cần tìm: từ câu {q_start} đến câu {q_end}. Chỉ trích xuất những câu hỏi thực sự xuất hiện trong các ảnh được cung cấp này.

Yêu cầu định dạng: Trả về DUY NHẤT một mảng JSON thuần túy (JSON Array), KHÔNG bọc bất kỳ giải thích ngoài JSON:
[
  {{
    "question_number": <số thứ tự câu hỏi>,
    "question_type": "Gap-fill / Multiple choice / Matching / True-False-Not Given / Yes-No-Not Given",
    "question_text": "Tóm tắt nội dung câu hỏi hoặc câu có chỗ trống",
    "answer": "Đáp án chính thức trong sách (ví dụ: DW307YZ, hoặc B, hoặc TRUE)",
    "explanation": "Giải thích chi tiết bằng tiếng Việt vì sao chọn đáp án này, phân tích bẫy nếu có",
    "evidence": "Trích dẫn audio transcript (đối với Listening) hoặc câu dẫn chứng trong bài đọc (đối với Reading)",
    "keywords": ["từ", "khóa", "quan", "trọng"]
  }}
]"""

        success = False
        for attempt in range(max_retries):
            if success:
                break
            for model_name in FALLBACK_MODELS:
                try:
                    res = client.models.generate_content(
                        model=model_name,
                        contents=[prompt, *images]
                    )
                    text = res.text.strip()
                    if text.startswith("```json"):
                        text = text[7:]
                    if text.startswith("```"):
                        text = text[3:]
                    if text.endswith("```"):
                        text = text[:-3]
                    text = text.strip()

                    batch_data = json.loads(text)
                    if isinstance(batch_data, list):
                        all_questions.extend(batch_data)
                        print(f"    ✅ Lô {b_idx + 1}/{len(page_batches)}: Đã trích xuất {len(batch_data)} câu với {model_name}.")
                        success = True
                        break
                    else:
                        print(f"    ⚠️ Lô {b_idx + 1} ({model_name}): Kết quả không phải mảng JSON, đang thử lại...")
                except Exception as e:
                    err_msg = str(e)
                    print(f"    ❌ Lỗi khi gọi model {model_name} (lần thử {attempt + 1}/{max_retries}): {err_msg[:120]}")
                    time.sleep(2)
            if not success:
                time.sleep(3)

        time.sleep(1) # Nghỉ ngắn tránh rate limit

    # Loại bỏ trùng lặp theo question_number nếu có
    dedup = {}
    for q in all_questions:
        num = q.get("question_number")
        if num and q_start <= num <= q_end and num not in dedup:
            q["skill"] = skill
            q["part"] = part
            dedup[num] = q

    # Kiểm tra xem có câu nào bị thiếu trong khoảng [q_start, q_end] không
    missing_nums = [n for n in range(q_start, q_end + 1) if n not in dedup]
    if missing_nums:
        print(f"    🔍 Phát hiện thiếu các câu {missing_nums} trong {name}. Đang thực hiện tìm kiếm bổ sung...")
        for m_num in missing_nums:
            rec_q = recover_missing_question(m_num, pages, images_dir, skill, part, name)
            if rec_q:
                dedup[m_num] = rec_q

    sorted_questions = sorted(dedup.values(), key=lambda x: x.get("question_number", 0))
    print(f"  ✨ Tổng cộng {name}: {len(sorted_questions)}/{q_end - q_start + 1} câu hỏi được trích xuất hoàn chỉnh.")
    return sorted_questions

def extract_test(test_num: int, output_dir: str = "data", images_dir: str = "data/cambridge18_images", force: bool = False):
    if test_num not in TEST_CONFIGS:
        raise ValueError(f"Test {test_num} không hợp lệ! Chỉ hỗ trợ 1, 2, 3, 4.")

    config = TEST_CONFIGS[test_num]
    os.makedirs(output_dir, exist_ok=True)
    out_file = os.path.join(output_dir, f"cambridge18_test_{test_num}.json")

    print("=" * 65)
    print(f"🚀 BẮT ĐẦU TRÍCH XUẤT {config['title'].upper()}")
    print("=" * 65)

    test_data = {
        "test": test_num,
        "title": config["title"],
        "listening": [],
        "reading": [],
        "extracted_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    # Đọc dữ liệu cũ nếu có để tái sử dụng các phần đã trích xuất hoàn tất
    if os.path.exists(out_file) and not force:
        try:
            with open(out_file, "r", encoding="utf-8") as f:
                old_data = json.load(f)
                if isinstance(old_data, dict):
                    test_data["listening"] = old_data.get("listening", [])
                    test_data["reading"] = old_data.get("reading", [])
                    print(f"  📦 Đã nạp dữ liệu có sẵn từ {out_file}: Listening ({len(test_data['listening'])} câu), Reading ({len(test_data['reading'])} câu).")
        except Exception as e:
            print(f"  ⚠️ Không đọc được dữ liệu cũ: {e}")

    for sec in config["sections"]:
        q_start, q_end = sec["question_range"]
        expected_nums = set(range(q_start, q_end + 1))
        current_list = test_data["listening"] if sec["skill"] == "listening" else test_data["reading"]
        existing_part_nums = {q["question_number"] for q in current_list if q.get("part") == sec["part"]}

        if not force and expected_nums.issubset(existing_part_nums):
            print(f"  ⏩ Bỏ qua {sec['name']}: Đã có đủ {len(expected_nums)} câu ({q_start} - {q_end}).")
            continue

        q_list = extract_section(sec, images_dir)
        target_list = test_data["listening"] if sec["skill"] == "listening" else test_data["reading"]
        existing_map = {q["question_number"]: q for q in target_list}
        for q in q_list:
            existing_map[q["question_number"]] = q
        
        merged_list = [existing_map[num] for num in sorted(existing_map.keys())]
        if sec["skill"] == "listening":
            test_data["listening"] = merged_list
        else:
            test_data["reading"] = merged_list

        # Lưu lại ngay lập tức sau mỗi section
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)

    total_extracted = len(test_data["listening"]) + len(test_data["reading"])
    print("=" * 65)
    print(f"🎉 HOÀN THÀNH TEST {test_num}!")
    print(f"📁 File kết quả: {out_file}")
    print(f"📊 Thống kê: Listening ({len(test_data['listening'])} câu), Reading ({len(test_data['reading'])} câu) | Tổng: {total_extracted} câu.")
    print("=" * 65)
    return out_file

def main():
    parser = argparse.ArgumentParser(description="Trích xuất đáp án và giải thích Cambridge IELTS 18")
    parser.add_argument("--test", type=int, required=True, choices=[1, 2, 3, 4], help="Số thứ tự Test (1, 2, 3, 4)")
    parser.add_argument("--outdir", type=str, default="data", help="Thư mục xuất file JSON")
    parser.add_argument("--force", action="store_true", help="Trích xuất lại toàn bộ từ đầu, bỏ qua cache")
    args = parser.parse_args()

    extract_test(args.test, output_dir=args.outdir, force=args.force)

if __name__ == "__main__":
    main()
