from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def lessons_menu():

    keyboard = [

        [
            InlineKeyboardButton("📘 1-dars", callback_data="lesson1"),
            InlineKeyboardButton("📘 2-dars", callback_data="lesson2")
        ],

        [
            InlineKeyboardButton("📘 3-dars", callback_data="lesson3")
        ]

    ]

    return InlineKeyboardMarkup(keyboard)