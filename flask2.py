from flask import Flask, request, jsonify, render_template
import sqlite3
import requests
import datetime
import traceback
import os

app = Flask(__name__, static_folder="static")
DATABASE = 'messages.db'
# שים את הכתובת שלך כאן
DISCORD_WEBHOOK_URL = 'https://discordapp.com/api/webhooks/1343219036942766232/FiyKDjOhZ6K8_4nmmCh1CwhuOqc18x3ZuUXRIB_hJ30Vwrwtk8TjIbwY-48RGCmcVVV8'


def init_db():
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS messages (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                content TEXT,
                                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
            conn.commit()
    except sqlite3.Error as e:
        print(f"שגיאת אתחול מסד נתונים: {e}")


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/input_text', methods=['POST'])
def input_text():
    try:
        # הדפסת נתוני הבקשה לאבחון
        print("Received data:", request.get_json())

        data = request.get_json()

        # בדיקות תקינות מפורטות יותר
        if not data:
            print("No data received")
            return jsonify({'error': 'לא התקבלו נתונים'}), 400

        if 'text' not in data:
            print("Missing text field")
            return jsonify({'error': 'חסר שדה טקסט'}), 400

        text = data['text']

        # אימות תוכן ההודעה
        if not text or len(text.strip()) == 0:
            print("Empty text")
            return jsonify({'error': 'הטקסט לא יכול להיות ריק'}), 400

        # שליחת ההודעה לדיסקורד עם טיפול בשגיאות
        try:
            discord_response = requests.post(DISCORD_WEBHOOK_URL, json={"content": text}, timeout=10)
            discord_response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Discord communication error: {e}")
            return jsonify({'error': f'שגיאת תקשורת עם Discord: {str(e)}'}), 500

        # שמירת ההודעה במסד הנתונים
        try:
            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO messages (content) VALUES (?)", (text,))
                conn.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return jsonify({'error': f'שגיאת מסד נתונים: {str(e)}'}), 500

        return jsonify({'success': True, 'message': 'הטקסט נשלח בהצלחה'})

    except Exception as e:
        # הדפסת מעקב השגיאה המלא
        print("Unexpected error:")
        traceback.print_exc()
        return jsonify({'error': f'שגיאה לא צפויה: {str(e)}'}), 500


@app.route('/get_messages', methods=['GET'])
def get_messages():
    try:
        # שימוש ב-datetime.now עם UTC
        time_threshold = (datetime.datetime.now(datetime.UTC) - datetime.timedelta(minutes=30)).strftime(
            "%Y-%m-%d %H:%M:%S")

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT content, timestamp FROM messages WHERE timestamp >= ? ORDER BY timestamp DESC",
                           (time_threshold,))
            messages = cursor.fetchall()

        # המרת התוצאות לפורמט קריא
        formatted_messages = []
        for msg in messages:
            text = msg[0]
            timestamp = datetime.datetime.strptime(msg[1], "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M:%S")
            formatted_messages.append({"text": text, "timestamp": timestamp})

        return jsonify({"messages": formatted_messages})

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return jsonify({'error': f'שגיאת מסד נתונים: {str(e)}'}), 500


if __name__ == '__main__':
    init_db()
    app.run(debug=True)