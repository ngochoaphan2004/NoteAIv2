import os
import sys
import re
import json
import urllib.request
import genanki

# Ensure UTF-8 output on Windows console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

DECK_ID = 2026100901
DECK_NAME = "IELTS - NoteAI Master Deck"
MODEL_ID = 2026100902
OUTPUT_APKG = os.path.join("content", "assets", "IELTS_Master_Deck.apkg")

CSS = """
.card {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  text-align: center;
  color: #2b2b2b;
  background-color: #faf8f8;
  padding: 24px;
  border-radius: 12px;
}
.nightMode .card {
  color: #ebebec;
  background-color: #1a1a1c;
}
.badge {
  display: inline-block;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 3px 8px;
  border-radius: 999px;
  background-color: #e5e5e5;
  color: #555;
  margin-bottom: 16px;
}
.nightMode .badge {
  background-color: #333;
  color: #bbb;
}
.word {
  font-size: 32px;
  font-weight: 800;
  color: #284b63;
  margin-bottom: 6px;
}
.nightMode .word {
  color: #7b97aa;
}
.ipa {
  font-size: 16px;
  color: #666;
  font-style: italic;
  margin-bottom: 4px;
}
.nightMode .ipa {
  color: #aaa;
}
.pos {
  font-size: 13px;
  font-weight: 600;
  color: #888;
  margin-bottom: 12px;
}
.hint {
  font-size: 13px;
  color: #999;
  margin-top: 18px;
}
#answer {
  border: none;
  border-top: 1px dashed #ccc;
  margin: 18px 0;
}
.nightMode #answer {
  border-top-color: #444;
}
.meaning {
  font-size: 20px;
  font-weight: 700;
  color: #1a7f37;
  margin-bottom: 16px;
}
.nightMode .meaning {
  color: #3fb950;
}
.section {
  text-align: left;
  background: #ffffff;
  border: 1px solid #e1e4e8;
  border-radius: 8px;
  padding: 12px 16px;
  margin-top: 12px;
  font-size: 14px;
  line-height: 1.6;
}
.nightMode .section {
  background: #252528;
  border-color: #38383a;
}
.section-title {
  font-weight: 700;
  font-size: 12px;
  text-transform: uppercase;
  color: #777;
  margin-bottom: 6px;
}
.nightMode .section-title {
  color: #999;
}
.context-tag {
  font-size: 11px;
  color: #888;
  margin-top: 14px;
}
"""

anki_model = genanki.Model(
    MODEL_ID,
    "IELTS NoteAI Vocabulary",
    fields=[
        {"name": "Word"},
        {"name": "IPA"},
        {"name": "PartOfSpeech"},
        {"name": "VietnameseMeaning"},
        {"name": "CollocationsAndExamples"},
        {"name": "Context"},
    ],
    templates=[
        {
            "name": "Recognition (Word -> Meaning)",
            "qfmt": """
<div class="card">
  <div class="badge">IELTS Master Deck</div>
  <div class="word">{{Word}}</div>
  <div class="ipa">{{IPA}}</div>
  <div class="pos">{{PartOfSpeech}}</div>
  <div class="hint">Nhớ lại nghĩa, cụm từ & ví dụ...</div>
</div>
""",
            "afmt": """
<div class="card">
  <div class="badge">IELTS Master Deck</div>
  <div class="word">{{Word}}</div>
  <div class="ipa">{{IPA}}</div>
  <div class="pos">{{PartOfSpeech}}</div>
  <hr id="answer">
  <div class="meaning">{{VietnameseMeaning}}</div>
  {{#CollocationsAndExamples}}
  <div class="section">
    <div class="section-title">📌 Collocations & Ví Dụ:</div>
    <div>{{CollocationsAndExamples}}</div>
  </div>
  {{/CollocationsAndExamples}}
  {{#Context}}
  <div class="context-tag">📍 Nguồn: {{Context}}</div>
  {{/Context}}
</div>
""",
        }
    ],
    css=CSS,
)

def clean_md(text):
    if not text:
        return ""
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    return text.strip()

def parse_vocab_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Get title from frontmatter
    title_match = re.search(r"^title:\s*[\"']?([^\"'\n]+)[\"']?", content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else os.path.basename(file_path)

    # Get tags
    tags = ["ielts", "noteai"]
    tag_matches = re.findall(r"-\s*([a-zA-Z0-9_-]+)", content[:400])
    for t in tag_matches:
        if t.lower() not in ["title", "aliases", "tags"]:
            tags.append(t.lower())

    vocab_list = []
    # Find table rows
    # | STT | Từ Vựng | Phiên Âm (IPA) | Loại Từ | Nghĩa Tiếng Việt | Từ Đồng Nghĩa | Collocations & Ví Dụ Trong Đề Thi |
    table_lines = re.findall(r"^\|\s*\*\*?\d+\*\*?\s*\|(.+)\|", content, re.MULTILINE)
    for line in table_lines:
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 6:
            word = clean_md(parts[0])
            ipa = clean_md(parts[1])
            pos = clean_md(parts[2])
            meaning = clean_md(parts[3])
            synonyms = clean_md(parts[4])
            colloc = parts[5].replace("<br>", "<br/>").strip()
            
            vocab_list.append({
                "word": word,
                "ipa": ipa,
                "pos": pos,
                "meaning": meaning,
                "synonyms": synonyms,
                "collocations": colloc,
                "context": title,
                "tags": list(set(tags))
            })
        elif len(parts) >= 5:
            word = clean_md(parts[0])
            ipa = clean_md(parts[1])
            pos = clean_md(parts[2])
            meaning = clean_md(parts[3])
            colloc = parts[4].replace("<br>", "<br/>").strip()
            
            vocab_list.append({
                "word": word,
                "ipa": ipa,
                "pos": pos,
                "meaning": meaning,
                "synonyms": "",
                "collocations": colloc,
                "context": title,
                "tags": list(set(tags))
            })
    return vocab_list

def find_all_vocab():
    all_vocab = []
    for root, _, files in os.walk("content"):
        for file in files:
            if file.startswith("vocab-") and file.endswith(".md"):
                fp = os.path.join(root, file)
                all_vocab.extend(parse_vocab_file(fp))
    return all_vocab

def anki_connect_invoke(action, **params):
    request_data = json.dumps({"action": action, "version": 6, "params": params}).encode("utf-8")
    req = urllib.request.Request("http://localhost:8765", data=request_data)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if len(data) != 2:
                raise Exception("Phản hồi bất thường từ AnkiConnect")
            if "error" in data and data["error"] is not None:
                raise Exception(data["error"])
            return data["result"]
    except Exception as e:
        return None

def sync_via_ankiconnect(vocab_list):
    print("Kiểm tra kết nối AnkiConnect (http://localhost:8765)...")
    ver = anki_connect_invoke("version")
    if not ver:
        print("-> AnkiConnect không hoạt động hoặc Anki Desktop chưa mở.")
        return False

    print(f"-> Đã kết nối AnkiConnect v{ver} thành công!")
    # Đảm bảo duy nhất 1 Deck
    anki_connect_invoke("createDeck", deck=DECK_NAME)

    candidates = []
    for v in vocab_list:
        syn_html = f"<div style='margin:6px 0 10px 0; color:#0969da; font-size:14px'><b>🔄 Đồng nghĩa:</b> {v['synonyms']}</div>" if v.get("synonyms") else ""
        note = {
            "deckName": DECK_NAME,
            "modelName": "Basic",
            "fields": {
                "Front": f"<b>{v['word']}</b><br><span style='color:#666'>{v['ipa']}</span><br><i>{v['pos']}</i>",
                "Back": f"<b style='color:#1a7f37;font-size:18px'>{v['meaning']}</b>{syn_html}<div style='text-align:left;font-size:13px'>{v['collocations']}</div><br><span style='color:#888;font-size:11px'>Nguồn: {v['context']}</span>",
            },
            "tags": v["tags"]
        }
        candidates.append((v["word"], note))

    # Cập nhật trường Đồng nghĩa cho các thẻ đã tồn tại
    existing_cards = anki_connect_invoke("findNotes", query=f'deck:"{DECK_NAME}"')
    if existing_cards:
        notes_info = anki_connect_invoke("notesInfo", notes=existing_cards)
        if notes_info and isinstance(notes_info, list):
            word_to_id = {}
            for n in notes_info:
                f_val = n.get("fields", {}).get("Front", {}).get("value", "")
                m = re.search(r"<b>([^<]+)</b>", f_val)
                if m:
                    word_to_id[m.group(1).strip().lower()] = n["noteId"]
                clean_f = re.sub(r"<[^>]+>", " ", f_val).strip().lower()
                word_to_id[clean_f] = n["noteId"]
            
            updated_count = 0
            for v in vocab_list:
                w = v["word"].strip().lower()
                note_id = word_to_id.get(w)
                if note_id:
                    syn_html = f"<div style='margin:6px 0 10px 0; color:#0969da; font-size:14px'><b>🔄 Đồng nghĩa:</b> {v['synonyms']}</div>" if v.get("synonyms") else ""
                    anki_connect_invoke("updateNoteFields", note={
                        "id": note_id,
                        "fields": {
                            "Front": f"<b>{v['word']}</b><br><span style='color:#666'>{v['ipa']}</span><br><i>{v['pos']}</i>",
                            "Back": f"<b style='color:#1a7f37;font-size:18px'>{v['meaning']}</b>{syn_html}<div style='text-align:left;font-size:13px'>{v['collocations']}</div><br><span style='color:#888;font-size:11px'>Nguồn: {v['context']}</span>",
                        }
                    })
                    updated_count += 1
            if updated_count:
                print(f"-> Đã cập nhật trường Đồng nghĩa cho {updated_count} thẻ hiện có trong deck.")

    notes_to_check = [c[1] for c in candidates]
    can_add_list = anki_connect_invoke("canAddNotes", notes=notes_to_check)
    if can_add_list is None:
        can_add_list = [True] * len(candidates)

    valid_candidates = [c for c, can_add in zip(candidates, can_add_list) if can_add]

    if valid_candidates:
        notes_batch = [vc[1] for vc in valid_candidates]
        batch_res = anki_connect_invoke("addNotes", notes=notes_batch)
        if batch_res and isinstance(batch_res, list):
            added_count = sum(1 for r in batch_res if r is not None)
            print(f"-> Đã thêm {added_count} thẻ mới vào deck '{DECK_NAME}'.")
        else:
            added_count = 0
            for w, n in valid_candidates:
                res = anki_connect_invoke("addNote", note=n)
                if res is not None:
                    added_count += 1
            print(f"-> Đã thêm {added_count} thẻ mới vào deck '{DECK_NAME}'.")
    else:
        print(f"-> Tất cả {len(candidates)} từ vựng đã tồn tại đầy đủ trong deck '{DECK_NAME}'.")

    deck_notes = anki_connect_invoke("findNotes", query=f'deck:"{DECK_NAME}"')
    total_count = len(deck_notes) if deck_notes else 0
    print(f"📊 Tổng số thẻ hiện tại trong deck: {total_count} thẻ.")

    # Tự động gọi lệnh sync lên AnkiWeb
    print("-> Đang kích hoạt đồng bộ lên AnkiWeb...")
    sync_res = anki_connect_invoke("sync")
    print("-> Đã gửi lệnh sync thành công!")
    return True

def generate_apkg(vocab_list):
    print(f"Đang đóng gói file Anki (.apkg) với DUY NHẤT 1 Deck: '{DECK_NAME}'...")
    deck = genanki.Deck(DECK_ID, DECK_NAME)
    
    for v in vocab_list:
        colloc_content = v["collocations"]
        if v.get("synonyms"):
            colloc_content = f"<b>🔄 Đồng nghĩa:</b> {v['synonyms']}<br/><br/>" + colloc_content
        note = genanki.Note(
            model=anki_model,
            fields=[
                v["word"],
                v["ipa"],
                v["pos"],
                v["meaning"],
                colloc_content,
                v["context"],
            ],
            tags=v["tags"],
        )
        deck.add_note(note)

    os.makedirs(os.path.dirname(OUTPUT_APKG), exist_ok=True)
    package = genanki.Package(deck)
    package.write_to_file(OUTPUT_APKG)
    print(f"-> Đã tạo thành công gói Anki tại: {OUTPUT_APKG} ({len(vocab_list)} thẻ)")

def main():
    vocab_list = find_all_vocab()
    print(f"Đã trích xuất tổng cộng {len(vocab_list)} từ vựng từ các ghi chú.")
    
    # 1. Luôn xuất file .apkg chuẩn với duy nhất 1 Deck
    generate_apkg(vocab_list)
    
    # 2. Thử đồng bộ trực tiếp qua AnkiConnect nếu có
    connected = sync_via_ankiconnect(vocab_list)
    if not connected:
        print("\n[MẸO]: Để tự động push 100% lên AnkiWeb:")
        print("  1. Mở Anki Desktop trên máy tính.")
        print("  2. Cài Add-on AnkiConnect (Mã: 2055492188).")
        print("  3. Đăng nhập tài khoản AnkiWeb trong Anki Desktop -> Lần sau script sẽ tự động push & sync lên AnkiWeb!")

if __name__ == "__main__":
    main()
