import sqlite3

import config

dbpath = config.Environment.dbpath


def init():
    conn = sqlite3.connect(dbpath)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            nickname TEXT NOT NULL,
            pfp TEXT NOT NULL,
            text TEXT NOT NULL
        )
    ''')
    cursor.execute('''
           CREATE TABLE IF NOT EXISTS chats (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               chat_id INTEGER,
               title TEXT,
               back TEXT NOT NULL DEFAULT "def",
               waiting bool DEFAULT FALSE
           )
       ''')

    conn.commit()
    conn.close()


def insert_task(chat_id, nickname, pfp, text):
    conn = sqlite3.connect(dbpath)
    cursor = conn.cursor()

    cursor.execute('''INSERT INTO tasks (chat_id, nickname, pfp, text) values (?, ?, ?, ?)''',
                   (chat_id, nickname, pfp, text))

    conn.commit()
    conn.close()


def get_all_tasks(chat_id):
    conn = sqlite3.connect(dbpath)
    cursor = conn.cursor()

    cursor.execute('''SELECT * FROM tasks WHERE chat_id = ?''',
                   (chat_id,))

    tasks = cursor.fetchall()

    messages = []

    for i in tasks:
        message = {"author": i[2], "avatar": i[3], "text": i[4].replace("\n", "<br>")}
        messages.append(message)

    conn.commit()
    conn.close()

    return messages


def clear_all_tasks(chat_id):
    conn = sqlite3.connect(dbpath)
    cursor = conn.cursor()

    cursor.execute('''DELETE FROM tasks WHERE chat_id = ? ''',
                   (chat_id,))

    conn.commit()
    conn.close()


def insert_chat(chat_id, title):
    conn = sqlite3.connect(dbpath)
    cursor = conn.cursor()

    cursor.execute('''INSERT INTO chats (chat_id, title) values (?, ?)''',
                   (chat_id, title))

    conn.commit()
    conn.close()


def set_chat_waiting(chat_id, waiting):
    conn = sqlite3.connect(dbpath)
    cursor = conn.cursor()

    cursor.execute('''UPDATE chats SET waiting = ? where chat_id = ?   ''',
                   (waiting, chat_id))

    conn.commit()
    conn.close()


def set_chat_back(chat_id, back):
    conn = sqlite3.connect(dbpath)
    cursor = conn.cursor()

    cursor.execute('''UPDATE chats SET back = ?,  waiting = 0 where chat_id = ?   ''',
                   (back, chat_id))

    conn.commit()
    conn.close()


def get_chat(chat_id):
    conn = sqlite3.connect(dbpath)

    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM chats WHERE chat_id = ?''',
                   (chat_id,))

    chat = cursor.fetchall()[0]

    conn.commit()
    conn.close()

    return chat


def get_chat_bg(chat_id):
    conn = sqlite3.connect(dbpath)
    cursor = conn.cursor()

    cursor.execute('''SELECT * FROM chats WHERE chat_id = ?''',
                   (chat_id,))

    chat = cursor.fetchall()[0]
    conn.commit()
    conn.close()

    return chat[3]
