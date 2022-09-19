import sqlite3
import os
import requests
import time
from telebot import TeleBot
from bs4 import BeautifulSoup as bs
from sqlite3 import Error

# Import -------------------------------


# connect func
def create_connection(path):
    connection_ = None
    try:
        connection_ = sqlite3.connect(path, check_same_thread=False)
        print('Connection DB == True')
    except Error as ex:
        print(f'DB error: {ex}')

    return connection_


connection = create_connection(os.path.abspath('base//base.sqlite'))


# add to database
def execute_query(connection_, query):
    cursor = connection_.cursor()
    try:
        cursor.execute(query)
        connection_.commit()
        print("Query executed successfully")
    except Error as ex:
        print(f"The execute_query '{ex}' occurred")


# create database
# create_lots_table = """
# CREATE TABLE lots (
# id INTEGER PRIMARY KEY AUTOINCREMENT,
# lot_number INT,
# date_time TEXT,
# lot_status TEXT,
# lot_url TEXT
# );
# """
#
# execute_query(connection, create_lots_table)

# read database
def execute_read_query(connection, query):
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except Error as ex:
        print(f'Read DB error: {ex}')

# Base -----------------------------------

def check_url_func(main_url, lot_number):
    # get page
    r = requests.get(main_url)

    # create variable for list
    td_text = []

    # take main elem from page
    soup = bs(r.text, 'html.parser')
    full_table = soup.find_all('table', class_='table table-info')
    for text in full_table:
        td_text = text.get_text().split()

    # take date and time
    date_time = td_text[0]
    date_time = str(date_time[0:10] + ' ' + date_time[10:])

    print(date_time)

    # del time and date from list
    del td_text[0]

    status = ''
    # take str from list
    for text in td_text:
        if text in status:
            if text != 'в':
                break
        status += text + ' '

    print(status)
    # write to DB
    return lot_number, date_time, status, main_url


# def to check repeat
def repeat_check(lot_number):
    new_lot_num = lot_number
    take_info = """
    SELECT *
    FROM lots
    """
    log_info = execute_read_query(connection, take_info)
    for info in log_info:
        id = info[0] - 1
        lot_num = log_info[id]
        if new_lot_num in lot_num:
            print('Не будет добавленно')
            return False

    return True


def write_to_base(lot_number, date_time, lot_status, lot_url):
    try:
        add_info = f"""
        INSERT INTO
        lots (lot_number, date_time, lot_status, lot_url)
        VALUES
        ('{lot_number}', '{date_time}', '{lot_status}', '{lot_url}')
        """
        execute_query(connection, add_info)
    except Exception as ex:
        print(f'Ошибка DB {ex}')


def update_in_base(date_time, lot_status):
    update_info = f"""
    UPDATE lots
    SET date_time = {date_time}, lot_status = {lot_status}
    """
    execute_query(connection, update_info)


def check_updates(lot_info):
    print(lot_info)

    # get page
    url = lot_info[4]
    r = requests.get(url)

    # create variable for list
    td_text = []

    # take main elem from page
    soup = bs(r.text, 'html.parser')
    full_table = soup.find_all('table', class_='table table-info')
    for text in full_table:
        td_text = text.get_text().split()

    date_time = td_text[0]
    date_time = str(date_time[0:10] + ' ' + date_time[10:])

    if str(lot_info[2]) == date_time:
        print(f'Ничего нового по партии {lot_info[1]}')
        return False
    else:
        info_for_update = check_url_func(url, lot_info[1])
        update_in_base(info_for_update[1], info_for_update[2])
        print(f'Данные обновились. Партия {lot_info[1]}')
        return True


# Telebot
bot = TeleBot('5716084391:AAFRXKoKk00NaRlnBUsY4sKhiKnJQemPoug')


# start func to bot
try:
    @bot.message_handler(content_types=['text'])
    def start_message(message):
        if 'партия' in message.text.lower():
            # message to list
            lot_options = message.text.split()
            lot_number = int(lot_options[1])
            main_url = str(lot_options[2])
            # check len of message
            if len(lot_options) != 3:
                bot.send_message(message.chat.id, 'Введите "Партия" | "Номер партии" | "URL" ')
            # check len of lots
            elif len(str(lot_number)) != 3 and len(str(lot_number)) != 4:
                bot.send_message(message.chat.id, 'Длина номера партии для SFX - 4 симв. \nДлина номера партии для BWW - 3 симв.')

            # checks repeat
            repeat = repeat_check(lot_number)
            if repeat:
                # take info of url
                info_for_base = check_url_func(main_url, lot_number)
                write_to_base(info_for_base[0], info_for_base[1], info_for_base[2], info_for_base[3])

        # Check updates
        time.sleep(7200)
        take_info = """
        SELECT *
        FROM lots
        """
        log_info = execute_read_query(connection, take_info)
        for info in log_info:
            id = info[0] - 1
            lot_info = log_info[id]
            update_point = check_updates(lot_info)
            if update_point:
                bot.send_message(message.chat.id, f'Изменения по партии {lot_info[1]}. Статус - {lot_info[3]}')
            else:
                bot.send_message(message.chat.id, f'Изменений по партии {lot_info[1]} нет. Статус - {lot_info[3]}')


    bot.polling(non_stop=True)
except Exception as ex:
    print(f'Telebot error: {ex}')