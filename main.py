import os
import functools
import telebot
from telebot import types
from settings import *
from storage import RedisUserLocationStorage

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
user_storage = RedisUserLocationStorage()


class User:
    """
    Class will describe user
    Methods:
        tasks:
        -add_user_task
        -add_task_priority
        -add_task_due_date
        -check_if_task_name_exist

        places:
        -add_place_name
        -add_place_address
        -add_place_location
        -check_if_place_name_exist
        -remove_all_current_location
    """

    def __init__(self, user_id):
        self.user_id = user_id
        # tasks
        self.user_tasks = {}
        self.recent_added_task = 0
        self.task_counter = 0

        # palces
        self.user_places = {}
        self.recent_added_place_name = None
        self.places_counter = 0

    # task's methods
    def add_user_task(self, task_name):
        self.user_tasks[task_name] = {}
        self.recent_added_task = task_name
        self.places_counter += 1

    def add_task_priority(self, task_name, priority_number):
        self.user_tasks[task_name]['priority'] = priority_number

    def add_task_due_date(self, task_name, due_date):
        self.user_tasks[task_name]['due_date'] = due_date

    def delete_current_task(self, task_name):
        if not self.check_if_task_name_exist(task_name):
            del self.user_tasks[task_name]
            return True
        return False

    def check_if_task_name_exist(self, task_name):
        if task_name not in self.user_tasks:
            return True
        return False

    def remove_all_current_task(self):
        self.user_tasks.clear()
        self.recent_added_place_name = None
        self.places_counter = 0

    # place's methods
    def add_place_name(self, place_name):
        self.user_places[place_name] = {}
        self.recent_added_place_name = place_name
        self.places_counter += 1

    def add_place_address(self, place_name, place_address):
        self.user_places[place_name]['address'] = place_address

    def add_place_location(self, place_name, place_location):
        self.user_places[place_name]['location'] = {'latitude': place_location.latitude,
                                                    'longitude': place_location.longitude}

    def delete_current_place(self, place_name):
        if not self.check_if_place_name_exist(place_name):
            del self.user_places[place_name]
            return True
        return False

    def check_if_place_name_exist(self, place_name):
        if place_name not in self.user_places:
            return True
        return False

    def remove_all_current_location(self):
        self.user_places.clear()
        self.recent_added_place_name = None
        self.places_counter = 0

    @classmethod
    def user_creation(cls, user_data):
        user_instance = cls(user_data['user_id'])
        user_instance.user_tasks = user_data.get('user_tasks', {})
        user_instance.recent_added_task = user_data.get(
            'recent_added_task', None)
        user_instance.task_counter = user_data.get('task_counter', 0)

        user_instance.user_places = user_data.get('user_places', {})
        user_instance.recent_added_place_name = user_data.get(
            'recent_added_place_name', None)
        user_instance.places_counter = user_data.get('places_counter', 0)

        return user_instance

    @staticmethod
    def check_if_user_exist(message, user_storage):
        retrived_data = user_storage.retrived_user_data(message.chat.id)
        if not retrived_data:
            user_instance = User(message.chat.id)
            user_storage.update_user_data(user_instance)
        else:
            return User.user_creation(retrived_data)

# decorator for data
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
            elif func.__name__ == 'add_task_name':
                bot.register_next_step_handler(msg, add_task_name)
            elif func.__name__ == 'add_task_priority':
                bot.register_next_step_handler(msg, add_task_priority)
            elif func.__name__ == 'add_task_due_date':
                bot.register_next_step_handler(msg, add_task_due_date)

    return wrapper_input_data_validator


def create_keyboard(user, keyboard_entity, page_number=1):
    """
    Created keyboard for places list
    """
    # places in 1 row
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    page_interval = 10 * (page_number - 1)  # ten places per view

    if keyboard_entity == 'tasks':
        dict_to_show = user.user_tasks
    elif keyboard_entity == 'places':
        dict_to_show = user.user_places

    buttons = [types.InlineKeyboardButton(text=place, callback_data=keyboard_entity + '_' + place) for place in list(
        dict_to_show)[page_interval:page_interval + 10]]
    for button in buttons:
        keyboard.add(button)
    # back and forward buttons
    back_button = types.InlineKeyboardButton(
        text="<", callback_data=keyboard_entity + '_back')
    page_number = types.InlineKeyboardButton(
        text="Стр." + str(page_number), callback_data=page_number)
    forward_button = types.InlineKeyboardButton(
        text=">", callback_data=keyboard_entity + '_forward')
    keyboard.add(back_button, page_number, forward_button)
    return keyboard

def delete_button_keyboard(user, keyboard_entity, entity_name):
    """
    Fucntion will return keyabord with delete button
    """
    keyboard = types.InlineKeyboardMarkup()
    delete_button = types.InlineKeyboardButton(
        text="Удалить", callback_data=keyboard_entity + '_delete' + '_' + entity_name)

    keyboard.add(delete_button)
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
    reply_text = """
    Команды бота:
    /add_place – добавление нового места;
    /list_places – отображение добавленных мест;
    /reset_places - позволяет удалить все ваши добавленные локации;

    /add_task
    /list_tasks
    """
    # user creation
    User.check_if_user_exist(message, user_storage)
    # send response to user
    bot.send_message(message.chat.id, reply_text)


# add places
@bot.message_handler(commands=['add_place'])
def place_add(message):
    try:
        # check if user exists
        User.check_if_user_exist(message, user_storage)
        reply_text = "Укажите название места:"
        # send answer
        msg = bot.send_message(message.chat.id, reply_text)
        # register next step
        bot.register_next_step_handler(msg, add_place_name)
    except Exception as e:
        bot.reply_to(message, 'oooops, что-то пошло не так')


@input_data_validator
def add_place_name(message):
    try:
        # add place name
        chat_id = message.chat.id
        place_name = message.text
        user = User.check_if_user_exist(message, user_storage)
        if user.check_if_place_name_exist(place_name):
            user.add_place_name(place_name)
            user_storage.update_user_data(user)
            # next step
            reply_text = "Пожалуйста, укажите адрес или координаты места."
            msg = bot.send_message(message.chat.id, reply_text)
            # register next step
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
        # add place name
        chat_id = message.chat.id
        user = User.check_if_user_exist(message, user_storage)
        if message.content_type == 'location':
            user.add_place_location(
                user.recent_added_place_name, message.location)
            user_storage.update_user_data(user)
            reply_text = 'Место успешно добавлено'
            bot.send_message(chat_id, reply_text)
        elif message.content_type == 'text':
            user.add_place_address(user.recent_added_place_name, message.text)
            user_storage.update_user_data(user)
            reply_text = 'Место успешно добавлено'
            bot.send_message(chat_id, reply_text)
        else:
            # next step
            reply_text = "Вы указали неверный формат локации. Попробуем еще раз?"
            msg = bot.send_message(message.chat.id, reply_text)
            # register next step
            bot.register_next_step_handler(msg, add_place_location)
    except Exception as e:
        bot.reply_to(message, 'oooops, что-то пошло не так')


@bot.message_handler(commands=['add_task'])
def task_add(message):
    try:
        # check if user exists
        User.check_if_user_exist(message, user_storage)
        reply_text = "Укажите название задачи:"
        # send answer
        msg = bot.send_message(message.chat.id, reply_text)
        # register next step
        bot.register_next_step_handler(msg, add_task_name)
    except Exception as e:
        bot.reply_to(message, 'oooops, что-то пошло не так')

# add places

@input_data_validator
def add_task_name(message):
    try:
        chat_id = message.chat.id
        task_name = message.text
        user = User.check_if_user_exist(message, user_storage)
        if user.check_if_task_name_exist(task_name):
            user.add_user_task(task_name)
            user_storage.update_user_data(user)
            reply_text = "Пожалуйста, укажите приоритет задачи:"
            msg = bot.send_message(message.chat.id, reply_text)
            # register next step
            bot.register_next_step_handler(msg, add_task_priority)
        else:
            reply_text = "Такое название места уже есть, выбирете другое, пожалуйста."
            msg = bot.send_message(message.chat.id, reply_text)
            bot.register_next_step_handler(msg, add_task_name)
    except Exception as e:
        bot.reply_to(message, 'oooops, что-то пошло не так')

@input_data_validator
def add_task_priority(message):
    try:
        chat_id = message.chat.id
        priotity_number = int(message.text)
        user = User.check_if_user_exist(message, user_storage)
        user.add_task_priority(user.recent_added_task, priotity_number)
        user_storage.update_user_data(user)
        reply_text = "Пожалуйста, укажите желаемую дату выполнения:"
        msg = bot.send_message(message.chat.id, reply_text)
        # register next step
        bot.register_next_step_handler(msg, add_task_due_date)
    except Exception as e:
        bot.reply_to(message, 'oooops, что-то пошло не так')

@input_data_validator
def add_task_due_date(message):
    try:
        chat_id = message.chat.id
        due_date = message.text
        user = User.check_if_user_exist(message, user_storage)
        user.add_task_due_date(user.recent_added_task, due_date)
        user_storage.update_user_data(user)
        reply_text = "Задача успешно добавлена."
        msg = bot.send_message(message.chat.id, reply_text)
    except Exception as e:
        bot.reply_to(message, 'oooops, что-то пошло не так')


@bot.message_handler(commands=['list_places'])
def list_of_user_locations(message, edit_message=False, next_page=0):
    try:
        reply_text = ''
        chat_id = message.chat.id
        user = User.check_if_user_exist(message, user_storage)
        if user.user_places:
            reply_text += 'Места которые вы добавили:'
            keyboard_entity = "places"
            keyboard = create_keyboard(user, keyboard_entity)
            bot.send_message(message.chat.id, reply_text,
                             reply_markup=keyboard)
        else:
            reply_text += 'У вас пока нет сохранненых мест.'
            bot.send_message(message.chat.id, reply_text)
    except Exception as e:
        bot.reply_to(message, 'oooops, что-то пошло не так')


@bot.message_handler(commands=['list_tasks'])
def list_of_user_locations(message, edit_message=False, next_page=0):
    try:
        reply_text = ''
        chat_id = message.chat.id
        user = User.check_if_user_exist(message, user_storage)
        if user.user_tasks:
            reply_text += 'Задачи которые вы добавили:'
            keyboard_entity = "tasks"
            keyboard = create_keyboard(user, keyboard_entity)
            bot.send_message(message.chat.id, reply_text,
                             reply_markup=keyboard)
        else:
            reply_text += 'У вас пока нет сохранненых задач.'
            bot.send_message(message.chat.id, reply_text)
    except Exception as e:
        bot.reply_to(message, 'oooops, что-то пошло не так')


@bot.message_handler(commands=['reset_places'])
def delete_all_current_user_locations(message):
    try:
        chat_id = message.chat.id
        user = User.check_if_user_exist(message, user_storage)
        user.remove_all_current_location()
        user_storage.update_user_data(user)
        msg = bot.send_message(
            message.chat.id, 'Все ранее сохраненные локации, удалены')
    except Exception as e:
        bot.reply_to(message, 'oooops, что-то пошло не так')


@bot.callback_query_handler(func=lambda c: c.data in ['tasks_forward', 'tasks_back', 'places_forward', 'places_back'])
def callback_handler_back_forward_buttons(callback_query):
    try:
        reply_text = ''
        current_page = retrive_current_page(callback_query)
        user = User.check_if_user_exist(callback_query.message, user_storage)

        button_values = callback_query.data.split('_')
        if button_values[0] == 'tasks':
            reply_text += 'Задачи которые вы добавили:'
            keyboard_entity = button_values[0]
        elif button_values[0] == 'places':
            reply_text += 'Места которые вы добавили:'
            keyboard_entity = button_values[0]

        if button_values[1] == 'forward':
            next_page = current_page + 1
            keyboard = create_keyboard(
                user, keyboard_entity, page_number=next_page)
            bot.edit_message_text(reply_text, callback_query.message.chat.id,
                                  callback_query.message.message_id, reply_markup=keyboard)
        elif button_values[1] == 'back' and current_page > 1:
            next_page = current_page - 1
            keyboard = create_keyboard(
                user, keyboard_entity, page_number=next_page)
            bot.edit_message_text(reply_text, callback_query.message.chat.id,
                                  callback_query.message.message_id, reply_markup=keyboard)
    except Exception as e:
        bot.reply_to(message, 'oooops, что-то пошло не так')

@bot.callback_query_handler(func=lambda c: c.data.split('_')[1] in ['delete'])
def callback_handler_delete_button(callback_query):
    try:
        reply_text = ''
        message = callback_query.message
        user = User.check_if_user_exist(callback_query.message, user_storage)
        entity_type, command, entity_name = callback_query.data.split('_', 2)


        if entity_type == 'tasks':
            if user.delete_current_task(entity_name):
                 user_storage.update_user_data(user)
                 reply_text += 'Задача успешно "{0}" удалена'.format(entity_name)
        elif entity_type == 'places':
            if user.delete_current_place(entity_name):
                user_storage.update_user_data(user)
                reply_text += 'Место успешно "{0}" удалено'.format(entity_name)
        else:
            reply_text += 'oooops, что-то пошло не так'

        bot.send_message(message.chat.id, reply_text)

    except Exception as e:
        bot.reply_to(message, 'oooops, что-то пошло не так')


@bot.callback_query_handler(func=lambda c: True)
def callback_handler(callback_query):
    """
    Callback handler for places detailed keyboard
    """
    try:
        message = callback_query.message
        entity_type, entity_name = callback_query.data.split('_', 1)
        user = User.check_if_user_exist(message, user_storage)

        if entity_type == 'tasks':
            if entity_name in user.user_tasks:
                reply_text = 'Детали задачи:\n'
                reply_text += 'Название задачи: ' + \
                    str(entity_name) + '\n'
                if 'priority' in user.user_tasks[entity_name]:
                    reply_text += "Приоритет задачи: " + \
                        str(user.user_tasks[entity_name]
                            ['priority']) + '\n'
                if 'due_date' in user.user_tasks[entity_name]:
                    reply_text += "Желаемое время выполнения: " + \
                        str(user.user_tasks[entity_name]['due_date'])
                keyboard = delete_button_keyboard(user, "tasks", entity_name)
                bot.send_message(message.chat.id, reply_text, reply_markup=keyboard)
        elif entity_type == 'places':
            if entity_name in user.user_places:
                reply_text = 'Детали места:\n'
                reply_text += 'Название места: ' + str(entity_name) + '\n'
                keyboard = delete_button_keyboard(user, "places", entity_name)

                if 'address' in user.user_places[entity_name]:
                    reply_text += "Адрес: " + \
                        str(user.user_places[entity_name]['address'])
                    bot.send_message(message.chat.id, reply_text, reply_markup=keyboard)
                elif 'location' in user.user_places[entity_name]:
                    reply_text += 'Локация места: '
                    lat = user.user_places[entity_name
                                           ]['location']['latitude']
                    lon = user.user_places[entity_name
                                           ]['location']['longitude']
                    bot.send_location(message.chat.id, lat, lon)
                    bot.send_message(message.chat.id, reply_text, reply_markup=keyboard)

    except Exception as e:
        bot.reply_to(message, 'oooops, что-то пошло не так')


if __name__ == '__main__':
    bot.polling()
