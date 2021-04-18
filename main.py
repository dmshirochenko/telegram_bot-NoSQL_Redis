import telebot
import json
import pickle
from telebot import types
from settings import *
import os


bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

user_dict = {}

class User:
    """
    Class will describe user
    """
    def __init__(self, user_id):
        self.user_id = user_id
        self.user_places = {}
        self.recent_added_place_name = None

    def add_place_name(self, place_name):
        self.user_places[place_name] = {}
        self.recent_added_place_name = place_name

    def check_if_place_name_exist(self, place_name):
        if place_name not in self.user_places:
            return True
        return False

    def add_place_address(self, place_name, place_address):
        self.user_places[place_name]['address'] = place_address

    def add_place_location(self, place_name, place_location):
        self.user_places[place_name]['location'] = {'latitude': place_location.latitude,
                                                    'longitude': place_location.longitude}

    def remove_all_current_location(self):
        self.user_places.clear()

    @classmethod
    def user_creation(cls, user_data):
        user_instance = cls(user_data['user_id'])
        user_instance.user_places = user_data['user_places']
        user_instance.recent_added_place_name = user_data['recent_added_place_name']

        return user_instance

    @staticmethod
    def check_if_user_exist(message, user_dict):
        if message.chat.id not in user_dict:
            user_instance = User(message.chat.id)
            user_dict[message.chat.id] = user_instance

def create_keyboard(user):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    buttons = [types.InlineKeyboardButton(text=place, callback_data=place) for place in user.user_places]
    keyboard.add(*buttons)
    return keyboard

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    reply_text ="""
    Команды бота:
    /add – добавление нового места;
    /list – отображение добавленных мест;
    /reset - позволяет удалить все ваши добавленные локации;
    /valentin_avgustinovich - нажми если ты Валя;
    /alexey_khoroshilov - нажми если ты Лёша.
    """
    #user creation
    User.check_if_user_exist(message, user_dict)
    #send response to user
    bot.send_message(message.chat.id, reply_text)

@bot.callback_query_handler(func=lambda x: True)
def callback_handler(callback_query):
    try:
        message = callback_query.message
        recieved_data = callback_query.data
        user = user_dict[message.chat.id]
        if recieved_data in user.user_places:
            reply_text = 'Детали места:\n'
            reply_text += 'Название места: ' + str(recieved_data) + '\n'
            if 'address' in user.user_places[recieved_data]:
                reply_text += "Адрес: " + str(user.user_places[recieved_data]['address'])
                bot.send_message(message.chat.id, reply_text)
            elif 'location' in user.user_places[recieved_data]:
                bot.send_message(message.chat.id, reply_text)
                lat = user.user_places[recieved_data]['location']['latitude']
                lon = user.user_places[recieved_data]['location']['longitude']
                bot.send_location(message.chat.id, lat, lon )
    except Exception as e:
        bot.reply_to(message, 'oooops, что-то пошло не так')


@bot.message_handler(commands=['list'])
def list_of_user_locations(message):
    try:
        reply_text = ''
        #check if user exists
        User.check_if_user_exist(message, user_dict)
        chat_id = message.chat.id
        user = user_dict[chat_id]
        if user.user_places:
            reply_text += 'Места которые вы добавили:'
            keyboard = create_keyboard(user)
            bot.send_message(message.chat.id, reply_text, reply_markup=keyboard)
        else:
            reply_text += 'У вас пока нет сохранненых мест.'
            bot.send_message(message.chat.id, reply_text)
    except Exception as e:
        bot.reply_to(message, 'oooops, что-то пошло не так')


@bot.message_handler(commands=['reset'])
def delete_all_current_user_locations(message):
    try:
        chat_id = message.chat.id
        user = user_dict[chat_id]
        user.remove_all_current_location()
        msg = bot.send_message(message.chat.id, 'Все ранее сохраненные локации, удалены')
    except Exception as e:
        bot.reply_to(message, 'oooops, что-то пошло не так')


@bot.message_handler(commands=['valentin_avgustinovich'])
def send_sticker(message):
    cwd = os.path.dirname(__file__)
    sti = open(os.path.join(cwd, 'sticker.webp'), 'rb')
    bot.send_sticker(message.chat.id, sti)


@bot.message_handler(commands=['alexey_khoroshilov'])
def send_sticker(message):
    cwd = os.path.dirname(__file__)
    sti = open(os.path.join(cwd, 'HP_1.webp'), 'rb')
    bot.send_sticker(message.chat.id, sti)
    sti = open(os.path.join(cwd, 'HP_2.webp'), 'rb')
    bot.send_sticker(message.chat.id, sti)
    sti = open(os.path.join(cwd, 'HP_3.webp'), 'rb')
    bot.send_sticker(message.chat.id, sti)
    sti = open(os.path.join(cwd, 'HP_4.webp'), 'rb')
    bot.send_sticker(message.chat.id, sti)
    sti = open(os.path.join(cwd, 'HP_1.webp'), 'rb')
    bot.send_sticker(message.chat.id, sti)
    #bot.send_sticker(message.chat.id, "FILEID")

@bot.message_handler(commands=['add'])
def send_add(message):
    try:
        #check if user exists
        User.check_if_user_exist(message, user_dict)
        reply_text = "Укажите название места:"
        #send answer
        msg = bot.send_message(message.chat.id, reply_text)
        #register next step
        bot.register_next_step_handler(msg, add_place_name)
    except Exception as e:
        bot.reply_to(message, 'oooops, что-то пошло не так')

def add_place_name(message):
    try:
        #add place name
        chat_id = message.chat.id
        place_name = message.text
        user = user_dict[chat_id]
        if user.check_if_place_name_exist(place_name):
            user.add_place_name(place_name)
            #next step
            reply_text = "Пожалуйста, укажите адрес или координаты места."
            msg = bot.send_message(message.chat.id, reply_text)
            #register next step
            bot.register_next_step_handler(msg, add_place_location)
        else:
            reply_text = "Такое название места уже есть, выбирете другое, пожалуйста."
            msg = bot.send_message(message.chat.id, reply_text)
            bot.register_next_step_handler(msg, add_place_name)
    except Exception as e:
        bot.reply_to(message, 'oooops, что-то пошло не так')


def add_place_location(message):
    try:
        #add place name
        chat_id = message.chat.id
        user = user_dict[chat_id]
        if message.content_type == 'location':
            user.add_place_location(user.recent_added_place_name, message.location)
            reply_text = 'Место успешно добавлено'
            bot.send_message(chat_id, reply_text)
        elif message.content_type == 'text':
            user.add_place_address(user.recent_added_place_name, message.text)
            reply_text = 'Место успешно добавлено'
            bot.send_message(chat_id, reply_text)
        else:
            #next step
            reply_text = "Вы указали неверный формат локации. Попробуем еще раз?"
            msg = bot.send_message(message.chat.id, reply_text)
            #register next step
            bot.register_next_step_handler(msg, add_place_location)
    except Exception as e:
        bot.reply_to(message, 'oooops, что-то пошло не так')


if __name__ == '__main__':
    bot.polling()
