import os
import requests
import threading
import time
from flask import Flask, request

app = Flask(__name__)

API_KEY = "0074455f628575a0f0a1650e42e12d1a"
BOT_TOKEN = "8760840819:AAGjJVBOM2JBK0RS7q9pQRFrea1myWTb0wU"
API_URL = "https://topsmm.uz/api/v2"
TG_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

KASPI_NUMBER = "7747 116 4091"
KASPI_NAME = "Аббос П"

RUB_TO_KZT = 5.8
NAZENKA = 1.20

ELDER = {
    "1956": {"ел": "🇨🇴 Колумбия", "баға_руб": 29.00},
    "1955": {"ел": "🇧🇩 Бангладеш", "баға_руб": 30.00},
    "1938": {"ел": "🇺🇿 Өзбекстан", "баға_руб": 71.00},
    "1957": {"ел": "🇲🇲 Мьянма", "баға_руб": 31.00},
    "1958": {"ел": "🇲🇿 Мозамбик", "баға_руб": 35.00},
    "1959": {"ел": "🇺🇸 АҚШ", "баға_руб": 35.00},
    "1960": {"ел": "🇰🇪 Кения", "баға_руб": 39.00},
    "1961": {"ел": "🇵🇱 Польша", "баға_руб": 39.00},
    "1962": {"ел": "🇮🇳 Үндістан", "баға_руб": 39.00},
}

for key in ELDER:
    rub = ELDER[key]["баға_руб"]
    tenge = rub * RUB_TO_KZT
    client_price = round(tenge * NAZENKA, -1)
    ELDER[key]["баға_client"] = f"{int(client_price)} ₸"

user_orders = {}
user_stats = {}

def send_message(chat_id, text, keyboard=None):
    data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if keyboard: data["reply_markup"] = keyboard
    requests.post(TG_URL + "sendMessage", json=data)

def topsmm_balance():
    return requests.post(API_URL, data={"key": API_KEY, "action": "balance"}).json()

def topsmm_buy(service_id):
    return requests.post(API_URL, data={"key": API_KEY, "action": "add", "service": service_id, "quantity": "1"}).json()

def topsmm_status(order_id):
    return requests.post(API_URL, data={"key": API_KEY, "action": "status", "order": order_id}).json()

def check_sms_loop(order_id):
    chat_id = user_orders[order_id]["chat_id"]
    el = user_orders[order_id]["el"]
    for i in range(30):
        time.sleep(10)
        status = topsmm_status(order_id)
        if status.get("status") == "Completed" and status.get("sms"):
            reply = f"<b>✅ АВТО КЕЛДІ!</b>\n\n<b>Ел:</b> {el['ел']}\n<b>Номер:</b> <code>{status['number']}</code>\n<b>Код:</b> <code>{status['sms']}</code>\n<b>Бағасы:</b> {el['баға_client']}"
            send_message(chat_id, reply)
            del user_orders[order_id]
            return

@app.route('/', methods=['POST'])
def webhook():
    update = request.get_json()
    if "message" in update and update["message"]["text"] == "/start":
        chat_id = update["message"]["chat"]["id"]
        keyboard = {"inline_keyboard": [[{"text": "📱 Номер Сатып алу", "callback_data": "menu_buy"}], [{"text": "💰 Баланс", "callback_data": "menu_balance"}, {"text": "📊 Статистика", "callback_data": "menu_stat"}], [{"text": "💳 Баланс толтыру", "callback_data": "menu_pay"}]]}
        send_message(chat_id, "<b>📱 АВТО Номер Боты</b>\n\nБағасы: ₸ Тенге + 20%", keyboard)

    if "callback_query" in update:
        chat_id = update["callback_query"]["message"]["chat"]["id"]
        data = update["callback_query"]["data"]
        if data == "menu_buy":
            keyboard = {"inline_keyboard": []}
            for key, val in ELDER.items(): keyboard["inline_keyboard"].append([{"text": f"{val['ел']} - {val['баға_client']}", "callback_data": f"buy_{key}"}])
            keyboard["inline_keyboard"].append([{"text": "⬅️ Артқа", "callback_data": "back_menu"}])
            send_message(chat_id, "<b>Елді таңда:</b>", keyboard)
        if data == "menu_balance": send_message(chat_id, f"<b>💰 Сайттағы Баланс:</b>\n<code>{topsmm_balance().get('balance', '0')} ₸</code>")
        if data == "menu_stat":
            stat = user_stats.get(chat_id, {"саны": 0, "жұмсады": 0})
            send_message(chat_id, f"<b>📊 Статистика:</b>\nСаны: <b>{stat['саны']}</b>\nЖұмсады: <b>{stat['жұмсады']} ₸</b>")
        if data == "menu_pay": send_message(chat_id, f"<b>💳 Баланс толтыру</b>\n\nКаспи: <code>{KASPI_NUMBER}</code>\nАлушы: <b>{KASPI_NAME}</b>\n\nЧекті @admin жібер")
        if data.startswith("buy_"):
            service_id = data.split("_")[1]; el = ELDER[service_id]
            send_message(chat_id, f"⏳ {el['ел']} {el['баға_client']} номері алынуда...")
            result = topsmm_buy(service_id)
            if result.get("order"):
                order_id = result["order"]; user_orders[order_id] = {"chat_id": chat_id, "el": el}
                price = int(el["баға_client"].replace(" ₸","")); user_stats[chat_id] = user_stats.get(chat_id, {"саны": 0, "жұмсады": 0}); user_stats[chat_id]["саны"] += 1; user_stats[chat_id]["жұмсады"] += price
                reply = f"<b>✅ Номер алынды!</b>\n<b>Ел:</b> {el['ел']}\n<b>Бағасы:</b> {el['баға_client']}\n<b>Номер:</b> <code>{result['number']}</code>\n\nКод күтілуде..."
                keyboard = {"inline_keyboard": [[{"text": "🔄 Қайта Тексеру", "callback_data": f"check_{order_id}"}]]}
                send_message(chat_id, reply, keyboard); threading.Thread(target=check_sms_loop, args=(order_id,)).start()
            else: send_message(chat_id, f"❌ Қате: {result.get('error')}")
        if data.startswith("check_"):
            order_id = data.split("_")[1]; status = topsmm_status(order_id)
            if status.get("sms"): send_message(chat_id, f"<b>✅ КОД:</b> <code>{status['sms']}</code>"); del user_orders[order_id]
            else: send_message(chat_id, "⏳ Код әлі жоқ")
        if data == "back_menu":
            keyboard = {"inline_keyboard": [[{"text": "📱 Номер Сатып алу", "callback_data": "menu_buy"}], [{"text": "💰 Баланс", "callback_data": "menu_balance"}, {"text": "📊 Статистика", "callback_data": "menu_stat"}], [{"text": "💳 Баланс толтыру", "callback_data": "menu_pay"}]]}
            send_message(chat_id, "<b>📱 АВТО Номер Боты</b>\n\nМенюден таңда:", keyboard)
    return "ok", 200

@app.route('/')
def home(): return "Smm-Kz-bot is running"
if __name__ == "__main__": app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
