import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import json

TOKEN = '7624076910:AAFtnSHskqlY_Aak_mfMkKwSB76c2fmm62s'
bot = telebot.TeleBot(TOKEN)

# Загружаем все маршруты
with open("route.json", encoding="utf-8") as f:
    ROUTES = json.load(f)

# Словари для хранения состояния
user_route = {}  # user_id -> route_id
user_step = {}  # user_id -> stop_index


# Получить маршрут по ID
def get_route(route_id):
    for route in ROUTES:
        if route["id"] == route_id:
            return route
    return None


@bot.message_handler(commands=['start'])
def main(message):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("Конечно", callback_data="start_walk"))
    markup.row(
        InlineKeyboardButton("Да", callback_data="start_walk"),
        InlineKeyboardButton("Само собой", callback_data="start_walk")
    )
    bot.send_message(
        message.chat.id,
        """🗺️ Привет!
Я — ваш персональный гид по Москве. Готов провести вас по увлекательным маршрутам, рассказать о тайнах старинных улиц, памятниках и скрытых жемчужинах столицы.

📍 Для начала выберите район Москвы, где вы находитесь. Я предложу маршруты и помогу пройти их шаг за шагом.

🚶‍♀️ Готовы начать прогулку?""",
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda c: c.data == "start_walk")
def choose_route(call):
    bot.answer_callback_query(call.id)
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(
        KeyboardButton("По центру Москвы"),
        KeyboardButton("10 главных достопримечательностей Москвы")
    )
    kb.row(
        KeyboardButton("От Кремля до Арбата"),
        KeyboardButton("ВДНХ: от арки до космоса")
    )
    bot.send_message(call.message.chat.id, "Выберите маршрут:", reply_markup=kb)



@bot.message_handler(func=lambda m: m.text in ["По центру Москвы", "10 главных достопримечательностей Москвы","От Кремля до Арбата","ВДНХ: от арки до космоса"])
def start_selected_route(message):
    route_map = {
        "По центру Москвы": "center_moscow",
        "10 главных достопримечательностей Москвы": "top_10_moscow",
        "От Кремля до Арбата": "kremlin_to_arbat",
        "ВДНХ: от арки до космоса": "vdnh_tour"
    }
    route_id = route_map[message.text]
    user_route[message.chat.id] = route_id
    user_step[message.chat.id] = 0
    send_stop(message.chat.id)


def send_stop(chat_id):
    route_id = user_route.get(chat_id)
    step = user_step.get(chat_id, 0)
    route = get_route(route_id)

    if not route or step >= len(route["stops"]):
        ikb = InlineKeyboardMarkup()
        ikb.add(InlineKeyboardButton("🔁 Начать заново", callback_data="start_walk"))
        bot.send_message(chat_id, "🎉 Экскурсия завершена! Хотите пройти другую?", reply_markup=ikb)
        return

    stop = route["stops"][step]
    with open(stop["photo"], "rb") as img:
        bot.send_photo(
            chat_id,
            img,
            caption=f"📍 *{stop['name']}*\n\n{stop['short_desc']}",
            parse_mode='Markdown'
        )

    ikb = InlineKeyboardMarkup()
    ikb.add(
        InlineKeyboardButton("📜 Подробнее", callback_data=f"more_{step}"),
        InlineKeyboardButton("➡️ Далее", callback_data=f"next_{step}")
    )
    ikb.add(InlineKeyboardButton("🗺 Открыть в Яндекс.Картах", url=stop["yandex_map_url"]))
    bot.send_message(chat_id, "Выберите действие:", reply_markup=ikb)


@bot.callback_query_handler(func=lambda c: c.data.startswith("more_"))
def show_more(call):
    step = int(call.data.split("_")[1])
    route_id = user_route.get(call.message.chat.id)
    route = get_route(route_id)
    history = route["stops"][step]["long_history"]
    parts = [history[i:i + 4000] for i in range(0, len(history), 4000)]

    for part in parts:
        bot.send_message(call.message.chat.id, part)

    ikb = InlineKeyboardMarkup()
    ikb.add(InlineKeyboardButton("➡️ Далее", callback_data=f"next_{step}"))
    bot.send_message(call.message.chat.id, "Готовы продолжить?", reply_markup=ikb)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith("next_"))
def next_step(call):
    step = int(call.data.split("_")[1]) + 1
    user_step[call.message.chat.id] = step
    bot.answer_callback_query(call.id)
    send_stop(call.message.chat.id)


bot.infinity_polling()

