import os
import functools
import telebot
from telebot import types
from settings import *
from storage import RedisUserLocationStorage


bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
user_storage = RedisUserLocationStorage()

user_dict = {}

class User:
    """
    Class will describe user
    Methods:
        -add_place_name
        -check_if_place_name_exist
        -add_place_address
        -add_place_location
        -remove_all_current_location
    """
    def __init__(self, user_id):
        self.user_id = user_id
        self.user_places = {}
        self.recent_added_place_name = None
        self.places_counter = 0


    def add_place_name(self, place_name):
        self.user_places[place_name] = {}
        self.recent_added_place_name = place_name
        self.places_counter += 1

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
        self.recent_added_place_name = None
        self.places_counter = 0

    @classmethod
    def user_creation(cls, user_data):
        user_instance = cls(user_data['user_id'])
        user_instance.user_places = user_data.get('user_places', {})
        user_instance.recent_added_place_name = user_data.get('recent_added_place_name', None)
        user_instance.places_counter = user_data.get('places_counter', 0)

        return user_instance

    @staticmethod
    def check_if_user_exist(message, user_storage):
        retrived_data = user_storage.retrived_user_data(message.chat.id)
        if not retrived_data:
            user_instance = User(message.chat.id)
            user_storage.update_user_data(user_instance)
            #user_dict[message.chat.id] = user_instance
        else:
            return User.user_creation(retrived_data)

#decorator for data
def input_data_validator(func):
        @functools.wraps(func)
        def wrapper_input_data_validator(message):
            if message.content_type in ['location'] and func.__name__ == 'add_place_location':
                return func(message)
            elif message.content_type in ['text'] and len(message.text) <= 64:
                return func(message)
            else:
                reply_text = """Слишком много знаков (больше 64) или неверный тип данных, попробуйте еще раз"""
                msg = bot.send_message(message.chat.id, reply_text)
                if func.__name__ == 'add_place_name':
                    bot.register_next_step_handler(msg, add_place_name)
                elif func.__name__ == 'add_place_location':
                    bot.register_next_step_handler(msg, add_place_location)

        return wrapper_input_data_validator


def create_keyboard(user, page_number = 1):
    """
    Created keyboard for places list
    """
    #places in 1 row
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    page_interval = 10 * (page_number - 1) #ten places per view
    buttons = [types.InlineKeyboardButton(text=place, callback_data=place) for place in list(user.user_places)[page_interval:page_interval + 10]]
    for button in buttons:
        keyboard.add(button)
    #back and forward buttons
    back_button = types.InlineKeyboardButton(text="<", callback_data='back')
    page_number = types.InlineKeyboardButton(text="Стр." + str(page_number), callback_data=page_number)
    forward_button = types.InlineKeyboardButton(text=">", callback_data='forward')
    keyboard.add(back_button, page_number,forward_button)
    return keyboard

def retrive_current_page(callback_query):
    """
    Function will current page info from reply_markup
    """
    page_button = callback_query.message.reply_markup.keyboard[-1][-2]
    page_value = int(page_button.callback_data)

    return int(page_value)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    reply_text ="""
    Команды бота:
    /add – добавление нового места;
    /list – отображение добавленных мест;
    /reset - позволяет удалить все ваши добавленные локации;
    """
    #user creation
    User.check_if_user_exist(message, user_storage)
    #send response to user
    bot.send_message(message.chat.id, reply_text)

@bot.message_handler(commands=['add'])
def send_add(message):
    try:
        #check if user exists
        User.check_if_user_exist(message, user_storage)
        reply_text = "Укажите название места:"
        #send answer
        msg = bot.send_message(message.chat.id, reply_text)
        #register next step
        bot.register_next_step_handler(msg, add_place_name)
    except Exception as e:
        bot.reply_to(message, 'oooops, что-то пошло не так')

@input_data_validator
def add_place_name(message):
    try:
        #add place name
        chat_id = message.chat.id
        place_name = message.text
        user = User.check_if_user_exist(message, user_storage)
        if user.check_if_place_name_exist(place_name):
            user.add_place_name(place_name)
            user_storage.update_user_data(user)
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

@input_data_validator
def add_place_location(message):
    try:
        #add place name
        chat_id = message.chat.id
        user = User.check_if_user_exist(message, user_storage)
        if message.content_type == 'location':
            user.add_place_location(user.recent_added_place_name, message.location)
            user_storage.update_user_data(user)
            reply_text = 'Место успешно добавлено'
            bot.send_message(chat_id, reply_text)
        elif message.content_type == 'text':
            user.add_place_address(user.recent_added_place_name, message.text)
            user_storage.update_user_data(user)
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

@bot.message_handler(commands=['list'])
def list_of_user_locations(message, edit_message = False, next_page = 0):
    try:
        reply_text = ''
        chat_id = message.chat.id
        user = User.check_if_user_exist(message, user_storage)
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
        user = User.check_if_user_exist(message, user_storage)
        user.remove_all_current_location()
        user_storage.update_user_data(user)
        msg = bot.send_message(message.chat.id, 'Все ранее сохраненные локации, удалены')
    except Exception as e:
        bot.reply_to(message, 'oooops, что-то пошло не так')


@bot.callback_query_handler(func=lambda c: c.data in ['back', 'forward'])
def callback_handler_back_forward_buttons(callback_query):
    try:
        reply_text = ''
        reply_text += 'Места которые вы добавили:'
        current_page = retrive_current_page(callback_query)
        user = User.check_if_user_exist(callback_query.message, user_storage)
        if callback_query.data == 'forward':
            next_page = current_page + 1
            keyboard = create_keyboard(user, page_number = next_page)
            bot.edit_message_text(reply_text, callback_query.message.chat.id, callback_query.message.message_id, reply_markup=keyboard)
        elif callback_query.data == 'back' and current_page > 1:
            next_page = current_page - 1
            keyboard = create_keyboard(user, page_number = next_page)
            bot.edit_message_text(reply_text, callback_query.message.chat.id, callback_query.message.message_id, reply_markup=keyboard)
    except Exception as e:
        bot.reply_to(message, 'oooops, что-то пошло не так')

@bot.callback_query_handler(func=lambda c: True)
def callback_handler(callback_query):
    """
    Callback handler for places detailed keyboard
    """
    try:
        message = callback_query.message
        recieved_data = callback_query.data
        user = User.check_if_user_exist(message, user_storage)
        if recieved_data in user.user_places:
            reply_text = 'Детали места:\n'
            reply_text += 'Название места: ' + str(recieved_data) + '\n'
            if 'address' in user.user_places[recieved_data]:
                reply_text += "Адрес: " + str(user.user_places[recieved_data]['address'])
                bot.send_message(message.chat.id, reply_text)
            elif 'location' in user.user_places[recieved_data]:
                reply_text += 'Локация места: '
                bot.send_message(message.chat.id, reply_text)
                lat = user.user_places[recieved_data]['location']['latitude']
                lon = user.user_places[recieved_data]['location']['longitude']
                bot.send_location(message.chat.id, lat, lon )
    except Exception as e:
        bot.reply_to(message, 'oooops, что-то пошло не так')

if __name__ == '__main__':
    bot.polling()
