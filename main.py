# -*- coding: utf-8 -*-
import os
import json
import telebot
import feedparser
import threading
import time
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

SOURCES = {
    "Українська правда (війна)": "https://www.pravda.com.ua/rss/view_war/",
    "Мілітарний": "https://militarny.com/feed/",
    "Генштаб ЗСУ": "https://www.mil.gov.ua/rss.xml",
}

DONATE_URL = "https://send.monobank.ua/jar/3PzEGicc2b"
SUBSCRIBERS_FILE = "subscribers.json"

def load_subscribers():
    try:
        with open(SUBSCRIBERS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_subscribers(subscribers):
    with open(SUBSCRIBERS_FILE, "w") as f:
        json.dump(subscribers, f)

def get_news(url, count=3):
    try:
        feed = feedparser.parse(url)
        news = []
        for entry in feed.entries[:count]:
            title = entry.get("title", "Без назви")
            link = entry.get("link", "")
            news.append(f"📰 {title}\n🔗 {link}")
        return news
    except:
        return []

def donate_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("💛 Підтримати бота", url=DONATE_URL))
    return keyboard

def send_morning_news():
    while True:
        now = datetime.now()
        if now.hour == 7 and now.minute == 0:
            subscribers = load_subscribers()
            if subscribers:
                text = "🌅 *Щоранкове зведення військових новин:*\n\n"
                for source, url in SOURCES.items():
                    news = get_news(url, 3)
                    if news:
                        text += f"📡 *{source}*:\n" + "\n\n".join(news) + "\n\n"
                for chat_id in subscribers:
                    try:
                        bot.send_message(chat_id, text, parse_mode="Markdown", disable_web_page_preview=True, reply_markup=donate_keyboard())
                    except Exception as e:
                        print(f"Помилка надсилання до {chat_id}: {e}")
            time.sleep(60)
        else:
            time.sleep(30)

@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    text = (
        "👋 Привіт! Я бот військових новин України.\n\n"
        "📋 Команди:\n"
        "/news — останні новини з усіх джерел\n"
        "/genshtab — зведення Генштабу ЗСУ\n"
        "/militarny — новини Мілітарного\n"
        "/pravda — Українська правда (війна)\n"
        "/subscribe — підписатись на щоранкові новини о 7:00\n"
        "/unsubscribe — відписатись від новин\n"
        "/donate — підтримати розвиток бота\n"
    )
    bot.reply_to(message, text)

@bot.message_handler(commands=["donate"])
def donate(message):
    bot.send_message(
        message.chat.id,
        "💛 Дякую за підтримку! Кожна гривня допомагає розвивати бота 🇺🇦",
        reply_markup=donate_keyboard()
    )

@bot.message_handler(commands=["subscribe"])
def subscribe(message):
    subscribers = load_subscribers()
    chat_id = message.chat.id
    if chat_id not in subscribers:
        subscribers.append(chat_id)
        save_subscribers(subscribers)
        bot.reply_to(message, "✅ Ти підписався на щоранкові новини о 7:00!")
    else:
        bot.reply_to(message, "ℹ️ Ти вже підписаний!")

@bot.message_handler(commands=["unsubscribe"])
def unsubscribe(message):
    subscribers = load_subscribers()
    chat_id = message.chat.id
    if chat_id in subscribers:
        subscribers.remove(chat_id)
        save_subscribers(subscribers)
        bot.reply_to(message, "❌ Ти відписався від щоранкових новин.")
    else:
        bot.reply_to(message, "ℹ️ Ти не був підписаний.")

@bot.message_handler(commands=["news"])
def all_news(message):
    bot.reply_to(message, "⏳ Збираю новини...")
    for source, url in SOURCES.items():
        news = get_news(url, 3)
        if news:
            text = f"📡 *{source}*:\n\n" + "\n\n".join(news)
            bot.send_message(message.chat.id, text, parse_mode="Markdown", disable_web_page_preview=True)
    bot.send_message(message.chat.id, "💛 Подобається бот? Підтримай розвиток!", reply_markup=donate_keyboard())

@bot.message_handler(commands=["genshtab"])
def genshtab_news(message):
    bot.reply_to(message, "⏳ Завантажую зведення Генштабу...")
    news = get_news(SOURCES["Генштаб ЗСУ"], 5)
    if news:
        text = "🪖 *Генштаб ЗСУ*:\n\n" + "\n\n".join(news)
        bot.send_message(message.chat.id, text, parse_mode="Markdown", disable_web_page_preview=True)
    else:
        bot.reply_to(message, "❌ Новини недоступні.")

@bot.message_handler(commands=["militarny"])
def militarny_news(message):
    bot.reply_to(message, "⏳ Завантажую новини Мілітарного...")
    news = get_news(SOURCES["Мілітарний"], 5)
    if news:
        text = "⚔️ *Мілітарний*:\n\n" + "\n\n".join(news)
        bot.send_message(message.chat.id, text, parse_mode="Markdown", disable_web_page_preview=True)
    else:
        bot.reply_to(message, "❌ Новини недоступні.")

@bot.message_handler(commands=["pravda"])
def pravda_news(message):
    bot.reply_to(message, "⏳ Завантажую новини УП...")
    news = get_news(SOURCES["Українська правда (війна)"], 5)
    if news:
        text = "📰 *Українська правда (війна)*:\n\n" + "\n\n".join(news)
        bot.send_message(message.chat.id, text, parse_mode="Markdown", disable_web_page_preview=True)
    else:
        bot.reply_to(message, "❌ Новини недоступні.")

if __name__ == "__main__":
    print("Бот військових новин запущений...")
    thread = threading.Thread(target=send_morning_news)
    thread.daemon = True
    thread.start()
    bot.infinity_polling()
