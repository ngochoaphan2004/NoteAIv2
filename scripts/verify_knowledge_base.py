import os
import sys
import re
import yaml
from datetime import datetime, date, timedelta

# Ensure UTF-8 output on Windows console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

CONTENT_DIR = "content"
ASSETS_DIR = os.path.join(CONTENT_DIR, "assets")

def normalize_slug(path_str):
    """Normalize path into standard Quartz slug format."""
    s = path_str.replace("\\", "/").strip("/")
    if s.endswith(".md"):
        s = s[:-3]
    return s

def get_all_notes_and_targets():
    """Scan content/ to build comprehensive index of valid slugs, aliases, and assets."""
    valid_slugs = set()
    alias_to_file = {}
    valid_assets = set()
    all_files = []

    # 1. Index static assets
    if os.path.exists(ASSETS_DIR):
        for root, _, files in os.walk(ASSETS_DIR):
            for f in files:
                rel = os.path.relpath(os.path.join(root, f), CONTENT_DIR).replace("\\", "/")
                valid_assets.add(rel)
                valid_assets.add("assets/" + f)
                valid_assets.add(f)

    # 2. Index markdown files & frontmatters
    for root, _, files in os.walk(CONTENT_DIR):
        for f in files:
            if f.endswith(".md"):
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, CONTENT_DIR).replace("\\", "/")
                slug = normalize_slug(rel_path)
                
                valid_slugs.add(slug)
                valid_slugs.add(slug + "/")
                valid_slugs.add(os.path.splitext(f)[0]) # Basename
                if slug.endswith("/index"):
                    valid_slugs.add(slug[:-6])
                    valid_slugs.add(slug[:-6] + "/")

                all_files.append((full_path, rel_path, slug))

                # Parse frontmatter for aliases
                try:
                    with open(full_path, "r", encoding="utf-8") as file:
                        text = file.read()
                    if text.startswith("---"):
                        parts = text.split("---", 2)
                        if len(parts) >= 3:
                            fm = yaml.safe_load(parts[1]) or {}
                            aliases = fm.get("aliases", [])
                            if isinstance(aliases, str):
                                aliases = [aliases]
                            for a in aliases:
                                a_clean = normalize_slug(str(a))
                                alias_to_file[a_clean] = slug
                                valid_slugs.add(a_clean)
                                valid_slugs.add(a_clean + "/")
                except Exception:
                    pass

    return all_files, valid_slugs, alias_to_file, valid_assets

def validate_frontmatter_schema(full_path, rel_path, auto_fix=False):
    """Enforce strict YAML Frontmatter Schema on each document."""
    errors = []
    warnings = []

    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()

    if not content.startswith("---"):
        errors.append("Thiếu YAML Frontmatter ở đầu file (phải bắt đầu bằng '---').")
        return errors, warnings, False

    parts = content.split("---", 2)
    if len(parts) < 3:
        errors.append("YAML Frontmatter chưa được đóng bằng '---'.")
        return errors, warnings, False

    try:
        fm = yaml.safe_load(parts[1]) or {}
    except Exception as e:
        errors.append(f"Cú pháp YAML không hợp lệ: {e}")
        return errors, warnings, False

    is_modified = False

    # 1. Validate 'title'
    title = fm.get("title")
    if not title or not isinstance(title, str) or not title.strip():
        errors.append("Trường 'title' là bắt buộc và phải là chuỗi Tiếng Việt không được để trống.")

    # 2. Validate 'tags'
    tags = fm.get("tags")
    if tags is None:
        errors.append("Trường 'tags' là bắt buộc (phải là danh sách phân loại).")
    elif not isinstance(tags, list) or len(tags) == 0:
        errors.append("Trường 'tags' phải là danh sách ít nhất 1 thẻ phân loại.")

    # 3. Specific rules for Vocabulary / Study / English documents
    is_vocab_or_lesson = (
        rel_path.startswith("plans/") or 
        os.path.basename(rel_path).startswith("vocab-") or 
        any(t in (tags or []) for t in ["vocabulary", "vocab", "listening", "reading", "writing", "speaking"])
    )

    if is_vocab_or_lesson and rel_path != "plans/index.md":
        # Check aliases
        aliases = fm.get("aliases")
        if aliases is None:
            if auto_fix:
                base_alias = os.path.splitext(os.path.basename(rel_path))[0]
                fm["aliases"] = [base_alias]
                is_modified = True
                warnings.append(f"Tự động bổ sung alias mặc định: '{base_alias}'")
            else:
                warnings.append("Khuyến nghị có trường 'aliases' cho tài liệu bài học để tối ưu hóa tìm kiếm & Wikilinks.")
        elif isinstance(aliases, list):
            note_slug = normalize_slug(rel_path)
            for a in aliases:
                if normalize_slug(str(a)) == note_slug:
                    errors.append(f"Alias '{a}' trùng với slug chính của file ({note_slug})! Điều này sẽ khiến Quartz tạo file redirect đè mất trang nội dung thực tế.")

        # Check sr-due (Spaced Repetition review date) for vocabulary files
        if os.path.basename(rel_path).startswith("vocab-"):
            sr_due = fm.get("sr-due")
            if not sr_due:
                if auto_fix:
                    # Default: review in 1 day
                    next_due = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
                    fm["sr-due"] = next_due
                    is_modified = True
                    warnings.append(f"Tự động đặt lịch Spaced Repetition 'sr-due': {next_due}")
                else:
                    warnings.append("File từ vựng nên có trường 'sr-due' (định dạng YYYY-MM-DD) để quản lý lịch ôn tập ngắt quãng.")
            elif isinstance(sr_due, (datetime, date)):
                # Valid date
                pass
            else:
                try:
                    datetime.strptime(str(sr_due).strip(), "%Y-%m-%d")
                except ValueError:
                    errors.append(f"Trường 'sr-due' ({sr_due}) không đúng định dạng chuẩn 'YYYY-MM-DD'.")

    if is_modified and auto_fix:
        # Re-serialize frontmatter cleanly
        new_fm_str = yaml.dump(fm, allow_unicode=True, sort_keys=False, default_flow_style=False)
        new_content = f"---\n{new_fm_str}---\n{parts[2].lstrip()}"
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(new_content)

    return errors, warnings, is_modified

def check_broken_links(full_path, rel_path, valid_slugs, valid_assets):
    """Scan file for broken [[Wikilinks]] and relative markdown links."""
    broken = []
    
    with open(full_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Skip frontmatter
    in_fm = False
    fm_count = 0
    start_line = 1

    for line_idx, line in enumerate(lines):
        line_num = line_idx + 1
        stripped = line.strip()

        if stripped == "---":
            fm_count += 1
            if fm_count == 2:
                in_fm = False
                continue
            elif fm_count == 1:
                in_fm = True
                continue
        if in_fm:
            continue

        # 1. Match wikilinks: [[target]] or ![[target]] or [[target|label]] or [[target#header]]
        wikilinks = re.findall(r"!?\[\[([^\]]+)\]\]", line)
        for raw in wikilinks:
            # strip anchor and alias
            target = raw.split("|")[0].split("#")[0].strip()
            if not target:
                continue

            target_slug = normalize_slug(target)

            # Check in assets
            if target_slug.startswith("assets/") or target_slug in valid_assets:
                continue
            # Check in notes/aliases
            if target_slug in valid_slugs:
                continue
            # Check relative from current folder
            cur_dir = os.path.dirname(rel_path).replace("\\", "/")
            if cur_dir:
                rel_target = normalize_slug(f"{cur_dir}/{target}")
                if rel_target in valid_slugs or rel_target in valid_assets:
                    continue

            broken.append({
                "line": line_num,
                "type": "Wikilink",
                "raw": f"[[{raw}]]",
                "target": target
            })

        # 2. Match standard relative markdown links [label](path)
        md_links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", line)
        for label, url in md_links:
            url_clean = url.strip()
            # Ignore web links and anchors
            if url_clean.startswith(("http://", "https://", "mailto:", "#")):
                continue

            url_path = url_clean.split("#")[0].split("?")[0].strip()
            # Quartz asset links should be vault-root relative (./assets/... or assets/...)
            if "assets/" in url_path and url_path.startswith("../"):
                broken.append({
                    "line": line_num,
                    "type": "Invalid Asset Link Format",
                    "raw": f"[{label}]({url})",
                    "target": "Đường dẫn asset không được dùng '../' (dùng './assets/...' để Quartz không nhảy ra ngoài website)"
                })
                continue

            # Resolve relative path from file directory
            cur_dir = os.path.dirname(full_path)
            resolved_fs_path = os.path.normpath(os.path.join(cur_dir, url_path))
            
            if not os.path.exists(resolved_fs_path):
                # Check if it resolves within content/
                content_resolved = os.path.normpath(os.path.join(CONTENT_DIR, url_path.lstrip("./")))
                if not os.path.exists(content_resolved):
                    broken.append({
                        "line": line_num,
                        "type": "Markdown Link",
                        "raw": f"[{label}]({url})",
                        "target": url_path
                    })

    return broken

def semantic_auto_link_concepts(target_file=None, dry_run=False):
    """Extract vocabulary and core IELTS concepts, then enrich notes with semantic Wikilinks."""
    all_files, valid_slugs, alias_to_file, _ = get_all_notes_and_targets()
    
    # 1. Build dictionary of concepts: {concept_name: target_slug}
    concepts = {}

    # Extract words from vocab files
    for full_path, rel_path, slug in all_files:
        if os.path.basename(rel_path).startswith("vocab-"):
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            # Find vocabulary words in table: | **1** | **uphill** | ...
            words = re.findall(r"\|\s*\*\*?\d+\*\*?\s*\|\s*\*\*?([a-zA-Z\s-]+)\*\*?\s*\|", content)
            for w in words:
                w_clean = w.strip().lower()
                if len(w_clean) > 3 and w_clean not in ["from", "this", "that", "with"]:
                    concepts[w_clean] = slug

    print(f"-> Thu thập được {len(concepts)} khái niệm/từ vựng học thuật để liên kết ngữ nghĩa.")

    # 2. Files to process
    files_to_process = []
    if target_file and os.path.exists(target_file):
        files_to_process = [(target_file, os.path.relpath(target_file, CONTENT_DIR), normalize_slug(target_file))]
    else:
        files_to_process = all_files

    total_links_inserted = 0

    for full_path, rel_path, slug in files_to_process:
        with open(full_path, "r", encoding="utf-8") as f:
            text = f.read()

        parts = text.split("---", 2)
        if len(parts) < 3:
            continue
        
        body = parts[2]
        modified_body = body
        links_in_file = 0

        for concept, target_slug in concepts.items():
            if target_slug == slug:
                continue # Don't link file to itself

            # Regex pattern to match whole word outside of existing links and brackets
            # Avoid matching if preceded by [[ or [ or followed by ]] or )
            pattern = re.compile(rf"(?<!\[\[)(?<!\[)(?<!/)\b({re.escape(concept)})\b(?![^\[]*\]\])(?!\))", re.IGNORECASE)
            
            # Check if match exists in non-code, non-heading areas
            matches = list(pattern.finditer(modified_body))
            if matches:
                # Replace only first occurrence to avoid over-linking
                m = matches[0]
                matched_str = m.group(1)
                replacement = f"[[{target_slug}|{matched_str}]]"
                
                # Check that it's not inside a heading (#) or code block
                line_start = modified_body.rfind("\n", 0, m.start()) + 1
                line = modified_body[line_start:modified_body.find("\n", m.end())]
                if not line.strip().startswith("#") and "```" not in line and "|" not in line:
                    modified_body = modified_body[:m.start()] + replacement + modified_body[m.end():]
                    links_in_file += 1
                    total_links_inserted += 1

        if links_in_file > 0 and not dry_run:
            new_content = f"---{parts[1]}---{modified_body}"
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"  ✨ Đã chèn {links_in_file} semantic wikilink vào: {rel_path}")

    print(f"-> Tổng cộng đã chèn {total_links_inserted} liên kết ngữ nghĩa vào Knowledge Graph.\n")
    return concepts

def run_verification(auto_fix=False):
    print("=" * 65)
    print(" 🛡️  ANTIGRAVITY FORMAL VERIFICATION & KNOWLEDGE GRAPH PIPELINE ")
    print("=" * 65)

    all_files, valid_slugs, alias_to_file, valid_assets = get_all_notes_and_targets()
    print(f"📂 Đã nạp: {len(all_files)} tài liệu Markdown | {len(valid_slugs)} Slugs/Aliases | {len(valid_assets)} Assets\n")

    total_errors = 0
    total_warnings = 0
    total_broken_links = 0
    files_modified = 0

    print("🔍 [1/2] Kiểm Tra Schema YAML Frontmatter...")
    for full_path, rel_path, slug in all_files:
        errors, warnings, modified = validate_frontmatter_schema(full_path, rel_path, auto_fix=auto_fix)
        if modified:
            files_modified += 1
        if errors or warnings:
            print(f"  📄 {rel_path}:")
            for e in errors:
                print(f"     ❌ LỖI: {e}")
                total_errors += 1
            for w in warnings:
                print(f"     ⚠️  CẢNH BÁO: {w}")
                total_warnings += 1

    if total_errors == 0:
        print("  ✅ Tất cả 100% tài liệu đáp ứng nghiêm ngặt YAML Frontmatter Schema!\n")
    else:
        print(f"\n  ❌ Phát hiện {total_errors} lỗi Schema Frontmatter cần khắc phục!\n")

    print("🔗 [2/2] Kiểm Tra Tính Toàn Vẹn Của Liên Kết (Broken Link Checker)...")
    for full_path, rel_path, slug in all_files:
        broken = check_broken_links(full_path, rel_path, valid_slugs, valid_assets)
        if broken:
            print(f"  📄 {rel_path}:")
            for b in broken:
                print(f"     🚨 Dòng {b['line']} [{b['type']}]: Mục tiêu '{b['target']}' KHÔNG TỒN TẠI! (Raw: {b['raw']})")
                total_broken_links += 1

    if total_broken_links == 0:
        print("  ✅ Không có bất kỳ Dead Link / Broken Wikilink nào trong toàn bộ đồ thị tri thức!\n")
    else:
        print(f"\n  ❌ Phát hiện {total_broken_links} liên kết hỏng (Dead Links) phá vỡ Knowledge Graph!\n")

    print("-" * 65)
    print(f"📊 TỔNG KẾT: {total_errors} Lỗi Schema | {total_broken_links} Dead Links | {total_warnings} Cảnh báo")
    if files_modified > 0:
        print(f"✨ Đã tự động chuẩn hóa & cập nhật {files_modified} file Markdown.")
    print("-" * 65)

    if total_errors > 0 or total_broken_links > 0:
        print("⛔ KẾT QUẢ: KHÔNG ĐẠT (Verification Failed) - Ngăn chặn Git Commit!")
        return False
    else:
        print("🎉 KẾT QUẢ: HOÀN TOÀN ĐẠT CHUẨN (Verification Passed) - Sẵn sàng xuất bản!")
        return True

if __name__ == "__main__":
    auto_fix = "--fix" in sys.argv
    if "--auto-link" in sys.argv:
        semantic_auto_link_concepts()
    success = run_verification(auto_fix=auto_fix)
    sys.exit(0 if success else 1)
