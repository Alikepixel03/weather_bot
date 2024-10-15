import requests
import telebot
import json
from telebot import types

weather_token = 'XXXXXXXXXXXXXXXXXXXXX'
api_token = "XXXXXXXXXXXXXXXXXXXXX"
bot = telebot.TeleBot(api_token)

weather_condition = {
    'clear': 'ясно',
    'partly-cloudy': 'малооблачно',
    'cloudy': 'облачно с прояснениями',
    'overcast': 'пасмурно',
    'drizzle': 'морось',
    'light-rain': 'небольшой дождь',
    'rain': 'дождь',
    'moderate-rain': 'умеренно сильный дождь',
    'heavy-rain': 'сильный дождь',
    'continuous-heavy-rain': 'длительный сильный дождь',
    'showers': 'ливень',
    'wet-snow': 'дождь со снегом',
    'light-snow': 'небольшой снег',
    'snow': 'снег',
    'snow-showers': 'снегопад',
    'hail': 'град',
    'thunderstorm': 'гроза',
    'thunderstorm-with-rain': 'дождь с грозой',
    'thunderstorm-with-hail': 'гроза с градом'
}


def fetch_weather(lat, lon):
    api_url = f'https://api.weather.yandex.ru/v2/informers?lat={lat}&lon={lon}&lang=ru_RU'
    headers = {"X-Yandex-API-Key": weather_token}
    res = requests.get(url=api_url, headers=headers)
    data = json.loads(res.text)
    return data["fact"]


@bot.message_handler(commands=['start'])
def get_message(message):
    user = login(message.from_user.id)
    print(user)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    city_list_button = types.KeyboardButton('Список городов')
    geo_button = types.KeyboardButton('Погода по геопозиции', request_location=True)
    history_button = types.KeyboardButton('История запросов')
    markup.add(city_list_button)
    markup.add(geo_button)
    markup.add(history_button)
    if user[1] == 'admin':
        add_city_button = types.KeyboardButton("Добавить город")
        delete_city_button = types.KeyboardButton("Удалить город")
        markup.add(add_city_button)
        markup.add(delete_city_button)
    return bot.send_message(message.chat.id, text=f'Привет!,{message.from_user.username}!\n\nВыберите команду:',
                            reply_markup=markup)


@bot.message_handler(content_types=['text'])
def get_button(message):
    print(message.text)
    markup = types.InlineKeyboardMarkup()
    if message.text == 'Список городов':
        all_cities = get_all_cities()
        print(all_cities)
        markup = types.InlineKeyboardMarkup()
        if all_cities:
            for city in all_cities:
                city_id, name, lon, lat = city[0], city[1], city[2], city[3]
                city_button = types.InlineKeyboardButton(name, callback_data=f'city_{name}_{lon}_{lat}_{city_id}')
                markup.add(city_button)
            return bot.send_message(message.chat.id, text='vibery gorod', reply_markup=markup)
        else:
            return bot.send_message(message.chat.id, text='Здесь ничего нет')
    elif message.text == 'История запросов':
        history = get_history_query(message.from_user.id)
        if not history:
            return bot.send_message(message.chat.id, text='Ничего не найдено, выбери другой способ')
        for city in history:
            city_id, name, lon, lat = city[0], city[1], city[2], city[3]
            city_button = types.InlineKeyboardButton(name, callback_data=f'city_{name}_{lon}_{lat}_{city_id}')
            markup.add(city_button)
        return bot.send_message(message.chat.id, text='Выбери город из истории', reply_markup=markup)
    else:
        return bot.send_message(message.chat.id, text='Что-то пошло не по плану жи ес, чиркани еще раз')


@bot.message_handler(content_types=['location'])
def handle_location(message):
    lat, lon = message.location.latitude, message.location.longitude
    fact = fetch_weather(lat, lon)
    if len(fact) == 1:
        return bot.send_message(message.chat.id, 'Problems on weather API')
    return bot.send_message(message.chat.id,
                            text=f'Ваша геопозиция, температура {fact["temp"]}°, чувствуется как {fact["feels_like"]}°. Сейчас на улице {weather_condition[fact["condition"]]}')


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    req = call.data.split('_')
    print(req)
    if req[0] == 'city':
        fact = fetch_weather(req[2], req[3])
        if len(fact) == 1:
            return bot.send_message(call.message.chat.id, 'Problems on weather API')
        print(call)
        insert_city_to_history(req[4], call.from_user.id)## получить айди пользователя
        return bot.send_message(call.message.chat.id,
                                text=f'{req[1]}, температура {fact["temp"]}°, чувствуется как {fact["feels_like"]}°. Сейчас на улице {weather_condition[fact["condition"]]}')


bot.polling(none_stop=True)
