import subprocess
import sys
import os

# Ensure UTF-8 output on Windows console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

def run_step(step_num, title, command, shell=True):
    print("\n" + "=" * 65)
    print(f"🚀 [Bước {step_num}/4] {title}")
    print("=" * 65)
    print(f"Lệnh: {command}\n")
    
    result = subprocess.run(command, shell=shell)
    if result.returncode != 0:
        print(f"\n❌ BƯỚC {step_num} THẤT BẠI! Lệnh thoát với mã lỗi: {result.returncode}")
        print("⛔ Quá trình tự động hóa bị hủy để bảo vệ tính toàn vẹn của Knowledge Graph!")
        sys.exit(1)
    print(f"\n✅ Bước {step_num} hoàn thành xuất sắc!")

def main():
    print("=" * 65)
    print(" 🛡️  ANTIGRAVITY FORMAL VERIFICATION & COMPILATION PIPELINE ")
    print("=" * 65)

    # Bước 1: Kiểm chứng Schema Frontmatter & Broken Link
    run_step(1, "Kiểm chứng Schema Frontmatter & Broken Link", "python scripts/verify_knowledge_base.py")

    # Bước 2: Markdownlint kiểm tra định dạng và layout
    run_step(2, "Markdown Linter & Format Verification", "npx markdownlint-cli \"content/**/*.md\" --config .markdownlint.json")

    # Bước 3: Đồng bộ Anki Master Deck
    run_step(3, "Đồng bộ Anki Master Deck (Single Deck Rule)", "python scripts/anki_sync.py")

    # Bước 4: Kiểm thử Quartz Website Build
    run_step(4, "Kiểm thử Quartz Website Compilation", "npx quartz build")

    print("\n" + "=" * 65)
    print("🎉 TOÀN BỘ PIPELINE HOÀN TOÀN THÀNH CÔNG! SẴN SÀNG COMMIT & PUSH!")
    print("=" * 65)

if __name__ == "__main__":
    main()

