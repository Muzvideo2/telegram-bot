import os
import requests
from flask import Flask, request
from datetime import datetime, timedelta
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Получаем переменные окружения
telegram_token = os.getenv("TELEGRAM_TOKEN")
bot_password = os.getenv("BOT_PASSWORD")

if not telegram_token or not bot_password:
    raise ValueError("Необходимо установить переменные окружения TELEGRAM_TOKEN и BOT_PASSWORD")

base_url = f"https://api.telegram.org/bot{telegram_token}"

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
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()  # Вызывает HTTPError, если был неудачный статус код
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при отправке сообщения в чат {chat_id}: {e}")

@app.route(f"/{telegram_token}", methods=["POST"])
def telegram_webhook():
    """
    Обрабатывает запросы от Telegram.
    """
    try:
        data = request.json
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "")
            logging.info(f"Получено сообщение от пользователя {chat_id}: {text}")
            
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
    except Exception as e:
        logging.error(f"Произошла ошибка при обработке запроса: {e}")
    
    return "OK"

def send_telegram_notification(question, user_vk_link):
    """
    Отправляет уведомление в Telegram о старте диалога.
    """
    try:
        # Определяем текущую дату и время в Омске (+6 часов к UTC)
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
            send_message(admin_id, message)
    except Exception as e:
        logging.error(f"Ошибка при отправке уведомления: {e}")

# Запуск Flask-приложения
if __name__ == "__main__":
    # Укажите вебхук
    webhook_url = f"https://<YOUR-SERVER-URL>/{telegram_token}"  # Замените на URL вашего сервера
    try:
        requests.get(f"{base_url}/setWebhook?url={webhook_url}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при установке вебхука: {e}")
    
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
