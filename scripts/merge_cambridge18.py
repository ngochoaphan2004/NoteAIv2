import os
import sys
import json
import time

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def merge_tests(data_dir: str = "data", output_file: str = "data/cambridge_18_answers_and_explanations.json"):
    all_data = {
        "title": "Cambridge IELTS 18 - Complete Answer Key & Detailed Explanations",
        "source": "Giải mã đề Cambridge IELTS 18 (IZONE - IELTS Chiến lược)",
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_tests": 4,
        "tests": {}
    }

    total_questions = 0
    missing_tests = []

    for test_num in [1, 2, 3, 4]:
        file_path = os.path.join(data_dir, f"cambridge18_test_{test_num}.json")
        if not os.path.exists(file_path):
            missing_tests.append(test_num)
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            t_data = json.load(f)

        test_key = f"test_{test_num}"
        all_data["tests"][test_key] = t_data

        listening_count = len(t_data.get("listening", []))
        reading_count = len(t_data.get("reading", []))
        total_questions += (listening_count + reading_count)

        print(f"✅ Đã nạp Test {test_num}: {listening_count} câu Listening | {reading_count} câu Reading")

    if missing_tests:
        print(f"⚠️ Chưa hoàn thành các Test: {missing_tests}")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 65)
    print(f"🎉 Đã hợp nhất dữ liệu thành công vào: {output_file}")
    print(f"📊 Tổng số câu hỏi hiện có: {total_questions} / 320 câu.")
    print("=" * 65)
    return all_data

if __name__ == "__main__":
    merge_tests()
