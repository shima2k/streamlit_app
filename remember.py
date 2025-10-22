import json, os

REMEMBER_FILE = "remember.json"

def save_login_info(username, password):
    try:
        with open(REMEMBER_FILE, "w", encoding="utf-8") as f:
            json.dump({"username": username, "password": password}, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print("❌ Lỗi khi lưu thông tin:", e)

def load_login_info():
    if os.path.exists(REMEMBER_FILE):
        try:
            with open(REMEMBER_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print("⚠️ Lỗi khi đọc file:", e)
    return {"username": "", "password": ""}
