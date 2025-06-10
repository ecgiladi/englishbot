from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from deep_translator import GoogleTranslator
import re

app = Flask(__name__)

# פונקציה להסרת ניקוד מהעברית
def remove_niqqud(text):
    return re.sub(r'[\u0591-\u05C7]', '', text)

# מבנה נתונים לכל משתמש
user_data = {}

@app.route("/bot", methods=["POST"])
def bot():
    incoming_msg = request.values.get('Body', '').strip()
    from_number = request.values.get('From', '')

    # אתחול משתמש חדש
    if from_number not in user_data:
        user_data[from_number] = {
            "mode": "normal",
            "translations": [],
            "quiz_index": 0
        }

    data = user_data[from_number]
    resp = MessagingResponse()

    # מצב בוחן
    if data["mode"] == "quiz":
        current_index = data["quiz_index"]
        correct_translation = data["translations"][current_index][1].strip()

        # בדיקת תשובה ללא ניקוד
        if remove_niqqud(incoming_msg) == remove_niqqud(correct_translation):
            msg = resp.message("✅ נכון!")
        else:
            msg = resp.message(f"❌ לא נכון. התשובה: {correct_translation}")

        data["quiz_index"] += 1

        if data["quiz_index"] >= len(data["translations"]):
            data["mode"] = "normal"
            data["translations"] = []
            data["quiz_index"] = 0
            resp.message("🎉 סיימת את הבוחן! אפשר להמשיך לתרגם מילים.")
        else:
            next_word = data["translations"][data["quiz_index"]][0]
            resp.message(f"שאלה {data['quiz_index']+1}: מה התרגום של '{next_word}'?")

        return str(resp)

    # מצב רגיל – תרגום
    try:
        translated = GoogleTranslator(source='en', target='iw').translate(incoming_msg)
    except Exception as e:
        resp.message(f"שגיאה בתרגום: {e}")
        return str(resp)

    data["translations"].append((incoming_msg, translated))
    resp.message(translated)

    # מעבר לבוחן אם יש 10 מילים
    if len(data["translations"]) == 10:
        data["mode"] = "quiz"
        data["quiz_index"] = 0
        first_word = data["translations"][0][0]
        resp.message("📝 התחלת בוחן! הנה שאלה ראשונה:")
        resp.message(f"שאלה 1: מה התרגום של '{first_word}'?")

    return str(resp)

if __name__ == "__main__":
    app.run(port=5000)
