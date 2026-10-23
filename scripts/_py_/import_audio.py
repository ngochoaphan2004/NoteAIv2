import os
import sys
import re
import shutil
import json

# Ensure UTF-8 output on Windows console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOURCE_DIR = r"D:\Ielts\Cambridge 18 - The IELTS Workshop\AUDIO FILES"
DEST_DIR = os.path.join(PROJECT_ROOT, "content", "assets", "audio")
METADATA_FILE = os.path.join(PROJECT_ROOT, "content", "assets", "audio_metadata.json")

PART_TOPICS = {
    (1, 1): {"title": "Transport Survey", "questions": "1 – 10"},
    (1, 2): {"title": "Voluntary Work Opportunities", "questions": "11 – 20"},
    (1, 3): {"title": "Talk on Careers in Fashion Design", "questions": "21 – 30"},
    (1, 4): {"title": "Elephant Communication & Behavior", "questions": "31 – 40"},
    
    (2, 1): {"title": "Joining a Running Club", "questions": "1 – 10"},
    (2, 2): {"title": "Regional Park Guide & Activities", "questions": "11 – 20"},
    (2, 3): {"title": "Student Presentation on Cities and Climate Change", "questions": "21 – 30"},
    (2, 4): {"title": "History of Tree Species in Scotland", "questions": "31 – 40"},
    
    (3, 1): {"title": "Customer Service & Bicycle Rental Inquiry", "questions": "1 – 10"},
    (3, 2): {"title": "Community Art Project & Local Museum", "questions": "11 – 20"},
    (3, 3): {"title": "Discussion on Wind Power Generation Study", "questions": "21 – 30"},
    (3, 4): {"title": "The Evolution of Language & Gestures", "questions": "31 – 40"},
    
    (4, 1): {"title": "Rental Property Inquiry & Agreement", "questions": "1 – 10"},
    (4, 2): {"title": "Zoo Tour & Wildlife Conservation", "questions": "11 – 20"},
    (4, 3): {"title": "University Seminar on Robotics and Healthcare", "questions": "21 – 30"},
    (4, 4): {"title": "Ancient Mesoamerican Agricultural Systems", "questions": "31 – 40"},
}

def main():
    print("=" * 65)
    print(" 🎧 NoteAI.v2 - Cambridge 18 Audio Importer & Metadata Generator ")
    print("=" * 65)

    if not os.path.exists(SOURCE_DIR):
        print(f"❌ Thư mục nguồn không tồn tại: {SOURCE_DIR}")
        sys.exit(1)

    os.makedirs(DEST_DIR, exist_ok=True)
    print(f"📁 Thư mục đích: {DEST_DIR}")

    audio_files_found = []

    for root, dirs, files in os.walk(SOURCE_DIR):
        for f in sorted(files):
            if not f.lower().endswith(".mp3"):
                continue

            full_path = os.path.join(root, f)
            parent_dir = os.path.basename(root)

            m_test = re.search(r"Test\s*(\d+)", parent_dir, re.I)
            test_num = int(m_test.group(1)) if m_test else None

            m_part = re.search(r"part\s*(\d+)", f, re.I)
            part_num = int(m_part.group(1)) if m_part else None

            if not test_num or not part_num:
                # Try fallback matching from filename
                m_t = re.search(r"section(\d+)", f, re.I)
                if m_t and not test_num:
                    test_num = int(m_t.group(1))

            if test_num and part_num:
                dest_filename = f"cam18-test{test_num}-part{part_num}.mp3"
                dest_path = os.path.join(DEST_DIR, dest_filename)
                
                audio_files_found.append({
                    "test": test_num,
                    "part": part_num,
                    "src": full_path,
                    "dest_path": dest_path,
                    "dest_filename": dest_filename,
                    "size": os.path.getsize(full_path)
                })

    print(f"🔍 Đã tìm thấy {len(audio_files_found)} file âm thanh MP3.")

    total_bytes = 0
    metadata = {
        "series": "Cambridge IELTS 18 Academic",
        "description": "Kho lưu trữ Audio nội bộ phục vụ luyện thi IELTS Listening cho NoteAI.v2",
        "total_tests": 4,
        "total_parts": len(audio_files_found),
        "base_url_relative": "assets/audio",
        "tests": {}
    }

    # Initialize tests dict
    for t in range(1, 5):
        metadata["tests"][str(t)] = {
            "test_number": t,
            "title": f"Cambridge 18 - Test {t} Listening",
            "total_questions": 40,
            "parts": {}
        }

    for item in audio_files_found:
        t = item["test"]
        p = item["part"]
        src = item["src"]
        dest = item["dest_path"]
        fname = item["dest_filename"]
        size = item["size"]
        size_mb = round(size / (1024 * 1024), 2)
        total_bytes += size

        # Copy file if not exists or different size
        if not os.path.exists(dest) or os.path.getsize(dest) != size:
            print(f"  📥 Đang sao chép: Test {t} Part {p} -> {fname} ({size_mb} MB)...")
            shutil.copy2(src, dest)
        else:
            print(f"  ⚡ Đã có sẵn: {fname} ({size_mb} MB)")

        topic_info = PART_TOPICS.get((t, p), {"title": f"Listening Part {p}", "questions": f"Part {p}"})

        metadata["tests"][str(t)]["parts"][str(p)] = {
            "part_number": p,
            "title": f"Part {p}: {topic_info['title']}",
            "topic": topic_info["title"],
            "questions": topic_info["questions"],
            "filename": fname,
            "relative_path": f"assets/audio/{fname}",
            "static_url": f"/static/audio/{fname}",
            "size_bytes": size,
            "size_mb": size_mb,
            "mime_type": "audio/mpeg"
        }

    total_mb = round(total_bytes / (1024 * 1024), 2)
    metadata["total_size_mb"] = total_mb

    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 65)
    print(f"✅ Hoàn tất import 100%! Tổng dung lượng: {total_mb} MB.")
    print(f"📄 Đã sinh file metadata tại: {METADATA_FILE}")
    print("=" * 65)

if __name__ == "__main__":
    main()

