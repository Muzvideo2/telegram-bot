# -*- coding: utf-8 -*-
"""Код телеграм-бота

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1cjriK8922lHUt4xz0rqMOgQp0lTtjzGu
"""



import requests
from flask import Flask, request
from datetime import datetime, timedelta

# Telegram API Token
telegram_token = "8101646300:AAE3hEx3q8953PHlfKiofvo4aH8zBBEUdrQ"
base_url = f"https://api.telegram.org/bot{telegram_token}"

# Секретный пароль
bot_password = "секретный_пароль"

# Список разрешённых пользователей
allowed_users = set()

# Словарь для отслеживания состояний пользователей
user_states = {}

# Flask-приложение
app = Flask(__name__)

def send_message(chat_id, text):
    """
    Отправляет сообщение пользователю.
    """
    url = f"{base_url}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    requests.post(url, data=data)

@app.route(f"/{telegram_token}", methods=["POST"])
def telegram_webhook():
    """
    Обрабатывает запросы от Telegram.
    """
    data = request.json
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        # Если пользователь отправляет /start
        if text == "/start":
            if chat_id in allowed_users:
                send_message(chat_id, "Вы уже авторизованы.")
            else:
                user_states[chat_id] = "waiting_password"
                send_message(chat_id, "Добро пожаловать! Пожалуйста, введите пароль для доступа.")
            return "OK"

        # Если пользователь вводит пароль
        if user_states.get(chat_id) == "waiting_password":
            if text == bot_password:
                allowed_users.add(chat_id)
                user_states[chat_id] = "authenticated"
                send_message(chat_id, "Пароль принят. Теперь вы можете пользоваться ботом!")
            else:
                send_message(chat_id, "Неверный пароль. Попробуйте снова.")
            return "OK"

        # Если пользователь авторизован
        if chat_id in allowed_users:
            send_message(chat_id, f"Вы отправили: {text}")
        else:
            send_message(chat_id, "У вас нет доступа. Используйте /start для ввода пароля.")

    return "OK"

def send_telegram_notification(question, user_vk_link):
    """
    Отправляет уведомление в Telegram о старте диалога.
    """
    # Определяем текущую дату и время в Омске (+3 часа к Москве)
    current_time = datetime.utcnow() + timedelta(hours=6)
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

    # Текст уведомления
    message = f"""
🕒 **Дата и время (Омск):** {formatted_time}
👤 **Стартовый вопрос:** {question}
🔗 **Ссылка на диалог:** {user_vk_link}
"""

    # Отправляем сообщение администратору
    for admin_id in allowed_users:  # Уведомление только авторизованным
        url = f"{base_url}/sendMessage"
        data = {
            "chat_id": admin_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        requests.post(url, data=data)

# Запуск Flask-приложения
if __name__ == "__main__":
    # Укажите вебхук
    webhook_url = f"https://<YOUR-SERVER-URL>/{telegram_token}"  # Замените на URL вашего сервера
    requests.get(f"{base_url}/setWebhook?url={webhook_url}")
    app.run(host="0.0.0.0", port=5000)