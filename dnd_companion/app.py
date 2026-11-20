import sys
import os
import io
import base64
import ctypes
import json
import urllib.request
import urllib.error
import webview
from webview.platforms import winforms as wf

try:
    import pypdf
except ImportError:
    pypdf = None

_window = None
_is_maximized = False

def extract_text_from_file_path(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == '.pdf':
        if not pypdf:
            raise RuntimeError("Modul pypdf belum terpasang.")
        reader = pypdf.PdfReader(path)
        pages_text = []
        for p in reader.pages:
            t = p.extract_text()
            if t:
                pages_text.append(t)
        return "\n".join(pages_text)
    else:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

def extract_text_from_pdf_bytes(pdf_bytes):
    if not pypdf:
        raise RuntimeError("Modul pypdf belum terpasang.")
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    return "\n".join([p.extract_text() or "" for p in reader.pages])

def get_default_api_key():
    env_k = os.environ.get("GEMINI_API_KEY", "").strip()
    if env_k:
        return env_k
    base = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(base, "api_key.txt"),
        os.path.join(os.path.dirname(base), "api_key.txt"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "api_key.txt")
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    k = f.read().strip()
                    if k:
                        return k
            except Exception:
                pass
    return ""

class Api:
    def set_on_top(self, val):
        global _window
        if _window:
            _window.on_top = bool(val)
            return True
        return False

    def minimize(self):
        global _window
        if _window:
            _window.minimize()
            return True
        return False

    def toggle_maximize(self):
        global _window, _is_maximized
        if _window:
            if _is_maximized:
                _window.restore()
                _is_maximized = False
            else:
                _window.maximize()
                _is_maximized = True
            return _is_maximized
        return False

    def resize_window(self, width, height):
        global _window
        if _window:
            w = max(340, min(1920, int(width)))
            h = max(480, min(1200, int(height)))
            _window.resize(w, h)
            return True
        return False

    def close(self):
        global _window
        if _window:
            try:
                _window.destroy()
            except Exception:
                pass
        import os
        os._exit(0)

    def move_window(self, x, y):
        global _window
        if _window:
            _window.move(int(x), int(y))
            return True
        return False

    def ask_ai(self, prompt, context="", custom_key=""):
        key = custom_key.strip() if custom_key and custom_key.strip() else get_default_api_key()
        models_to_try = ["gemini-flash-lite-latest", "gemini-3.8-flash", "gemini-3.5-flash", "gemini-flash-latest"]
        
        system_instruction = (
            "Kamu adalah D&D Companion AI cerdas, ramah, dan seru untuk pemain D&D 5e bernama Malexius. "
            "Karakter pemain: Malexius The One Who Defied Fate (Level 20: Rogue 17 / Fighter 2 / Wizard 1). "
            "Senjata utama: Vesper (The Whispering Rail-Cannon), Aegis Shield, Sneak Attack 9d6, Slayer Form. "
            "Kemampuan: Reliable Talent (semua skill proficient minimal d20 adalah 10), Action Surge, Second Wind, Cunning Action, Evasion. "
            "Gaya bahasa: Santai, antusias, seru, menguasai aturan D&D 5e (PHB/DMG), "
            "bisa memberikan narasi sinematik dramatis saat diminta, taktik cerdas, atau kalkulasi lemparan dadu. "
            "Gunakan format markdown yang rapi (bold, bullet points). Jika menyarankan lemparan dadu, tuliskan format [Roll: XdY+Z] agar pemain bisa langsung klik. Jawab dalam bahasa Indonesia santai."
        )
        
        full_prompt = f"{prompt}\n\n[Konteks Game/Roll Saat Ini]:\n{context}" if context else prompt
        
        payload = {
            "contents": [
                {
                    "parts": [{"text": f"System Context: {system_instruction}\n\nPertanyaan/Aksi Pemain: {full_prompt}"}]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 800
            }
        }
        data_bytes = json.dumps(payload).encode('utf-8')
        
        last_error = "Tidak ada model yang merespons."
        for m in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={key}"
            req = urllib.request.Request(url, data=data_bytes, headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=12) as resp:
                    res_data = json.loads(resp.read().decode('utf-8'))
                    candidates = res_data.get('candidates', [])
                    if candidates and 'content' in candidates[0]:
                        parts = candidates[0]['content'].get('parts', [])
                        if parts:
                            return {"success": True, "reply": parts[0].get('text', ''), "model": m}
            except Exception as e:
                last_error = str(e)
                continue
        return {"success": False, "error": f"Gagal menghubungi Gemini AI: {last_error}"}

    def pick_character_file(self):
        global _window
        if not _window:
            return {"success": False, "error": "Jendela tidak tersedia."}
        file_types = (
            'Character Sheets (*.pdf;*.txt;*.md)',
            'PDF files (*.pdf)',
            'Text/Markdown files (*.txt;*.md)',
            'All files (*.*)'
        )
        try:
            chosen = _window.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=False, file_types=file_types)
            if not chosen:
                return {"success": False, "cancelled": True}
            filepath = chosen[0] if isinstance(chosen, (list, tuple)) else chosen
            raw_text = extract_text_from_file_path(filepath)
            filename = os.path.basename(filepath)
            return {"success": True, "filename": filename, "text": raw_text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def extract_pdf_text_b64(self, b64_data):
        try:
            raw_b64 = b64_data.split(",", 1)[1] if "," in b64_data else b64_data
            pdf_bytes = base64.b64decode(raw_b64)
            text = extract_text_from_pdf_bytes(pdf_bytes)
            return {"success": True, "text": text}
        except Exception as e:
            return {"success": False, "error": f"Gagal mengekstrak PDF: {e}"}

    def parse_character_sheet(self, raw_text, custom_key=""):
        key = custom_key.strip() if custom_key and custom_key.strip() else get_default_api_key()
        models_to_try = ["gemini-flash-lite-latest", "gemini-3.8-flash", "gemini-3.5-flash", "gemini-flash-latest"]
        
        truncated_text = raw_text[:28000] if len(raw_text) > 28000 else raw_text
        prompt = (
            "You are an expert D&D 5e character sheet parser.\n"
            "Analyze the following raw character sheet text (from a PDF, TXT, or MD export) and extract all character stats into a clean, valid JSON object.\n"
            "Return ONLY the valid JSON object without markdown formatting, code fences, or explanations.\n\n"
            "Target JSON Schema:\n"
            "{\n"
            '  "id": "char_unique_id",\n'
            '  "name": "Character Name",\n'
            '  "subtitle": "Class & Level • Species / Subrace • Alignment",\n'
            '  "hp": 50,\n'
            '  "maxHp": 50,\n'
            '  "tempHp": 0,\n'
            '  "ac": 16,\n'
            '  "initMod": 3,\n'
            '  "speed": "30 ft",\n'
            '  "proficiency": 3,\n'
            '  "stats": {"STR": 10, "DEX": 16, "CON": 14, "INT": 12, "WIS": 10, "CHA": 14},\n'
            '  "saves": {"STR": 0, "DEX": 5, "CON": 2, "INT": 1, "WIS": 0, "CHA": 2},\n'
            '  "attacks": [\n'
            '    {\n'
            '      "name": "Weapon/Spell Name",\n'
            '      "type": "Melee / Ranged / Spell",\n'
            '      "atkBonus": 5,\n'
            '      "dice": {"d8": 1},\n'
            '      "dmgMod": 3,\n'
            '      "dmgType": "Piercing",\n'
            '      "desc": "1d8+3 Piercing (Finesse)"\n'
            '    }\n'
            '  ],\n'
            '  "skills": [\n'
            '    {"name": "Stealth", "mod": 7, "prof": true, "expertise": true, "reliable": false}\n'
            '  ],\n'
            '  "trackers": [\n'
            '    {"name": "Spell Slots (Lv 1)", "current": 4, "max": 4},\n'
            '    {"name": "Action Surge", "current": 1, "max": 1}\n'
            '  ],\n'
            '  "features": ["Sneak Attack 3d6", "Cunning Action"],\n'
            '  "notes": "Short summary of background or key magic items"\n'
            "}\n\n"
            "Raw Character Sheet Text:\n"
            f"{truncated_text}"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 2500
            }
        }
        data_bytes = json.dumps(payload).encode('utf-8')
        last_error = "Semua model gagal."
        for m in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={key}"
            req = urllib.request.Request(url, data=data_bytes, headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=20) as resp:
                    res_data = json.loads(resp.read().decode('utf-8'))
                    candidates = res_data.get('candidates', [])
                    if candidates and 'content' in candidates[0]:
                        parts = candidates[0]['content'].get('parts', [])
                        if parts:
                            raw_reply = parts[0].get('text', '').strip()
                            clean = raw_reply
                            if clean.startswith("```json"):
                                clean = clean[7:]
                            if clean.startswith("```"):
                                clean = clean[3:]
                            if clean.endswith("```"):
                                clean = clean[:-3]
                            parsed_char = json.loads(clean.strip())
                            if "id" not in parsed_char or not parsed_char["id"]:
                                import time
                                parsed_char["id"] = "char_" + str(int(time.time()))
                            return {"success": True, "character": parsed_char, "model": m}
            except Exception as e:
                last_error = str(e)
                continue
        return {"success": False, "error": f"Gagal memproses sheet dengan AI: {last_error}"}

    def pick_and_parse_character_sheet(self, custom_key=""):
        res = self.pick_character_file()
        if not res.get("success"):
            return res
        text = res.get("text", "")
        if not text.strip():
            return {"success": False, "error": "File kosong atau teks tidak terbaca."}
        parse_res = self.parse_character_sheet(text, custom_key=custom_key)
        if parse_res.get("success"):
            parse_res["filename"] = res.get("filename", "")
        return parse_res

def main():
    global _window
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    html_path = os.path.join(base_dir, "index.html")
    api = Api()
    
    window = webview.create_window(
        title="D&D Beyond Dice",
        url=f"file:///{html_path.replace(os.sep, '/')}",
        width=450,
        height=680,
        min_size=(350, 480),
        frameless=True,
        resizable=True,
        easy_drag=False,
        transparent=False,
        background_color='#101217',
        on_top=False,
        js_api=api
    )
    _window = window

    def on_shown():
        try:
            browser_form = wf.BrowserView.instances.get(window.uid)
            if browser_form:
                hwnd = browser_form.Handle.ToInt64()
                # Windows 11 rounded corners
                DWMWA_WINDOW_CORNER_PREFERENCE = 33
                DWMWCP_ROUND = 2
                val = ctypes.c_int(DWMWCP_ROUND)
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd,
                    DWMWA_WINDOW_CORNER_PREFERENCE,
                    ctypes.byref(val),
                    ctypes.sizeof(val)
                )
        except Exception:
            pass

    window.events.shown += on_shown
    webview.start(debug=False)

if __name__ == "__main__":
    main()
