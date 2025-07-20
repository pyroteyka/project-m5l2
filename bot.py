import telebot
from config import *
from logic import *

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, "Привет! Я бот, который может показывать города на карте. Напиши /help для списка команд.")

@bot.message_handler(commands=['help'])
def handle_help(message):
    bot.send_message(message.chat.id, "Доступные команды:  `/start` - начать работу с ботом и получить приветственное сообщение."
    "`/help` - получить список доступных команд."
    "`/show_city <city_name>` - отобразить указанный город на карте."
    "`/remember_city <city_name>` - сохранить город в список избранных."
    "`/show_my_cities` - показать все сохраненные города.")
    # Допиши команды бота


@bot.message_handler(commands=['show_city'])
def handle_show_city(message):
    city_name = message.text.split()[-1]
    mapper = DB_Map(db_path='database.db')

def show_city(update, context):
    """
    Показывает на карте один город и его координаты.
    Используется, например, команда /show_city <город>.
    """
    # Получаем название города из команды
    args = context.args
    if not args:
        update.message.reply_text("📝 Укажи, пожалуйста, название города: /show_city <город>")
        return

    city = " ".join(args).title()  # Нормализуем капитализацию

    # Получаем координаты
    coords = mapper.get_coordinates(city)
    if not coords:
        update.message.reply_text(f"❌ Не нашёл город «{city}» в базе.")
        return

    lat, lon = coords

    # Создаём карту с одним маркером
    img_path = f'/tmp/city_{update.effective_user.id}_{city}.png'
    mapper.create_graph(img_path, [city])

    # Отправляем карту
    with open(img_path, 'rb') as f:
        update.message.reply_photo(f, caption=f"📍 Город: {city}\nШирота: {lat:.4f}, Долгота: {lon:.4f}")



@bot.message_handler(commands=['remember_city'])
def handle_remember_city(message):
    user_id = message.chat.id
    city_name = message.text.split()[-1]
    if manager.add_city(user_id, city_name):
        bot.send_message(message.chat.id, f'Город {city_name} успешно сохранен!')
    else:
        bot.send_message(message.chat.id, 'Такого города я не знаю. Убедись, что он написан на английском!')

@bot.message_handler(commands=['show_my_cities'])
def handle_show_visited_cities(message):
    cities = manager.select_cities(message.chat.id)
    # предположим, есть глобальный экземпляр mapper
mapper = DB_Map(db_path='database.db')  # или как у вас устроено

def show_my_cities(update, context):
    """
    Обработчик команды /show_my_cities.
    """
    user_id = update.effective_user.id

    # Получаем список городов для пользователя из БД
    conn = mapper.conn  # либо по-другому
    cur = conn.cursor()
    cur.execute("SELECT city FROM user_cities WHERE user_id = ?", (user_id,))
    rows = cur.fetchall()
    if not rows:
        update.message.reply_text("У тебя пока нет сохранённых городов. Добавь через команду /add_city <название>.")
        return

    cities = [row[0] for row in rows]
    cities_text = "\n".join(f"• {c}" for c in cities)

    # 1. Показываем список
    update.message.reply_text(f"Вот твои города:\n{cities_text}")

    # 2. Строим карту
    img_path = f'/tmp/my_cities_{user_id}.png'
    mapper.create_graph(img_path, cities)

    # 3. Отправляем изображение
    with open(img_path, 'rb') as f:
        update.message.reply_photo(f, caption="Твоя карта с городами 📍")



if __name__=="__main__":
    manager = DB_Map(DATABASE)
    bot.polling()
