import os
import requests
from flask import Flask, request, jsonify  # Исправлено: добавлен импорт jsonify
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

# >>> Набор для "паузы" по имени_фамилии
paused_names = set()

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
            if text.startswith("/clear "):
                name_to_clear = text.replace("/clear ", "").strip()
                if name_to_clear:
                    response = requests.post(
                       f"https://muzvideo2-bot.onrender.com/clear_context/{quote(name_to_clear)}"
                    )
                    if response.status_code == 200:
                        send_message(chat_id, f"Контекст для пользователя {name_to_clear} успешно удалён.")
                    else:
                        send_message(chat_id, f"Ошибка при удалении контекста для пользователя {name_to_clear}.")
                else:
                    send_message(chat_id, "Формат команды: /clear Имя_Фамилия")
                return "OK"
            if text.startswith("/pause "):
                name_to_pause = text.replace("/pause ", "").strip()
                if name_to_pause:
                    paused_names.add(name_to_pause)
                    send_message(chat_id, f"Поставил на паузу: {name_to_pause}")
                else:
                    send_message(chat_id, "Формат команды: /pause Имя_Фамилия")
                return "OK"

            elif text.startswith("/play "):
                name_to_play = text.replace("/play ", "").strip()
                if name_to_play in paused_names:
                    paused_names.remove(name_to_play)
                    send_message(chat_id, f"Возобновил для: {name_to_play}")
                else:
                    send_message(chat_id, f"Пользователь '{name_to_play}' не был на паузе.")
                return "OK"

            send_message(chat_id, f"Вы отправили: {text}")
        else:
            send_message(chat_id, "У вас нет доступа. Используйте /start для ввода пароля.")

    return "OK"

@app.route("/is_paused/<name>", methods=["GET"])
def check_pause(name):
    """
    Проверяет, находится ли пользователь на паузе.
    """
    if name in paused_names:
        return jsonify({"paused": True})  # Исправлено: добавлен импорт jsonify
    return jsonify({"paused": False})

def send_telegram_notification(question, user_vk_link):
    """
    Отправляет уведомление в Telegram о старте диалога.
    """
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
    render_url = os.getenv("RENDER_EXTERNAL_URL")  # URL вашего Render
    if render_url:
        webhook_url = f"{render_url}/{telegram_token}"
        requests.get(f"{base_url}/setWebhook?url={webhook_url}")
        print(f"Webhook установлен: {webhook_url}")
    else:
        print("Ошибка: URL сервиса не найден.")

    # Запуск Flask
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
