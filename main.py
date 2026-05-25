# -*- coding: utf-8 -*-
import os
import json
import telebot
import feedparser
import threading
import time
import requests
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ALARM_API_KEY = os.environ.get("ALARM_API_KEY")
bot = telebot.TeleBot(BOT_TOKEN)

SOURCES = {
    "Українська правда (війна)": "https://www.pravda.com.ua/rss/view_war/",
    "Армія Inform": "https://armyinform.com.ua/feed/",
    "Google News (війна України)": "https://news.google.com/rss/search?q=війна+Україна&hl=uk&gl=UA&ceid=UA:uk",
}

DONATE_URL = "https://send.monobank.ua/jar/3PzEGicc2b"
BOT_LINK = "https://t.me/ua_military_news_bot"
ALERTS_MAP = "https://alerts.in.ua"
SUBSCRIBERS_FILE = "subscribers.json"
ALARM_SUBSCRIBERS_FILE = "alarm_subscribers.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

active_alerts = set()

def load_subscribers():
    try:
        with open(SUBSCRIBERS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_subscribers(subscribers):
    with open(SUBSCRIBERS_FILE, "w") as f:
        json.dump(subscribers, f)

def load_alarm_subscribers():
    try:
        with open(ALARM_SUBSCRIBERS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_alarm_subscribers(subscribers):
    with open(ALARM_SUBSCRIBERS_FILE, "w") as f:
        json.dump(subscribers, f)

def get_news(url, count=3):
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        feed = feedparser.parse(response.content)
        if not feed.entries:
            print(f"[WARNING] Немає записів у фіді: {url}")
            return []
        news = []
        for entry in feed.entries[:count]:
            title = entry.get("title", "Без назви")
            link = entry.get("link", "")
            news.append(f"📰 {title}\n🔗 {link}")
        return news
    except Exception as e:
        print(f"[ERROR] Помилка парсингу {url}: {e}")
        return []

def get_alerts():
    try:
        headers = {"Authorization": ALARM_API_KEY}
        response = requests.get("https://api.ukrainealarm.com/api/v3/alerts", headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[ERROR] Помилка отримання тривог: {e}")
        return []

def check_alerts():
    global active_alerts
    while True:
        try:
            alerts_data = get_alerts()
            current_alerts = set()

            if isinstance(alerts_data, list):
                for region_data in alerts_data:
                    region = region_data.get("regionName", "Невідома область")
                    active = region_data.get("activeAlerts", [])
                    for alert in active:
                        if alert.get("type") == "AIR":
                            current_alerts.add(region)

            # Нові тривоги
            new_alerts = current_alerts - active_alerts
            for region in new_alerts:
                subscribers = load_alarm_subscribers()
                for chat_id in subscribers:
                    try:
                        bot.send_message(
                            chat_id,
                            f"🚨 *ПОВІТРЯНА ТРИВОГА!*\n\n📍 {region}\n\n⚠️ Негайно перейдіть до укриття!",
                            parse_mode="Markdown"
                        )
                    except Exception as e:
                        print(f"Помилка надсилання тривоги: {e}")

            # Відбій тривоги
            ended_alerts = active_alerts - current_alerts
            for region in ended_alerts:
                subscribers = load_alarm_subscribers()
                for chat_id in subscribers:
                    try:
                        bot.send_message(
                            chat_id,
                            f"✅ *ВІДБІЙ ТРИВОГИ*\n\n📍 {region}\n\nМожна виходити з укриття.",
                            parse_mode="Markdown"
                        )
                    except Exception as e:
                        print(f"Помилка надсилання відбою: {e}")

            active_alerts = current_alerts

        except Exception as e:
            print(f"[ERROR] Помилка перевірки тривог: {e}")

        time.sleep(30)

def donate_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("💛 Підтримати бота", url=DONATE_URL))
    return keyboard

def main_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(KeyboardButton("📰 Всі новини"), KeyboardButton("🪖 Армія Inform"))
    keyboard.row(KeyboardButton("🌐 Google News"), KeyboardButton("📋 Українська правда"))
    keyboard.row(KeyboardButton("🚨 Підписатись на тривоги"), KeyboardButton("🔕 Відписатись від тривог"))
    keyboard.row(KeyboardButton("✅ Підписатись на новини"), KeyboardButton("❌ Відписатись від новин"))
    keyboard.row(KeyboardButton("🗺️ Карта тривог"), KeyboardButton("📤 Поділитись ботом"))
    keyboard.row(KeyboardButton("🚀 Головне меню"), KeyboardButton("💛 Підтримати бота"))
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

def welcome_message(chat_id):
    text = (
        "👋 *Привіт! Я бот військових новин України* 🇺🇦\n\n"
        "Я збираю свіжі новини та сповіщаю про повітряні тривоги:\n"
        "• 📰 Українська правда\n"
        "• 🪖 Армія Inform\n"
        "• 🌐 Google News\n"
        "• 🚨 Сповіщення про повітряні тривоги\n\n"
        "Обери що тебе цікавить 👇"
    )
    bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=main_keyboard())

@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    welcome_message(message.chat.id)

@bot.message_handler(func=lambda m: m.text == "🚀 Головне меню")
def go_home(message):
    welcome_message(message.chat.id)

@bot.message_handler(func=lambda m: m.text == "📰 Всі новини")
def all_news(message):
    bot.reply_to(message, "⏳ Збираю новини...")
    found_any = False
    for source, url in SOURCES.items():
        news = get_news(url, 3)
        if news:
            found_any = True
            text = f"📡 *{source}*:\n\n" + "\n\n".join(news)
            bot.send_message(message.chat.id, text, parse_mode="Markdown", disable_web_page_preview=True)
    if not found_any:
        bot.send_message(message.chat.id, "❌ Наразі новини недоступні. Спробуйте пізніше.")
    bot.send_message(message.chat.id, "💛 Подобається бот? Підтримай розвиток!", reply_markup=donate_keyboard())

@bot.message_handler(func=lambda m: m.text == "🪖 Армія Inform")
def armyinform_news(message):
    bot.reply_to(message, "⏳ Завантажую новини Армія Inform...")
    news = get_news(SOURCES["Армія Inform"], 5)
    if news:
        text = "🪖 *Армія Inform*:\n\n" + "\n\n".join(news)
        bot.send_message(message.chat.id, text, parse_mode="Markdown", disable_web_page_preview=True)
    else:
        bot.send_message(message.chat.id, "❌ Новини недоступні. Спробуйте пізніше.")
    bot.send_message(message.chat.id, "💛 Підтримай бота!", reply_markup=donate_keyboard())

@bot.message_handler(func=lambda m: m.text == "🌐 Google News")
def google_news(message):
    bot.reply_to(message, "⏳ Завантажую новини Google News...")
    news = get_news(SOURCES["Google News (війна України)"], 5)
    if news:
        text = "🌐 *Google News (війна України)*:\n\n" + "\n\n".join(news)
        bot.send_message(message.chat.id, text, parse_mode="Markdown", disable_web_page_preview=True)
    else:
        bot.send_message(message.chat.id, "❌ Новини недоступні. Спробуйте пізніше.")
    bot.send_message(message.chat.id, "💛 Підтримай бота!", reply_markup=donate_keyboard())

@bot.message_handler(func=lambda m: m.text == "📋 Українська правда")
def pravda_news(message):
    bot.reply_to(message, "⏳ Завантажую новини УП...")
    news = get_news(SOURCES["Українська правда (війна)"], 5)
    if news:
        text = "📰 *Українська правда (війна)*:\n\n" + "\n\n".join(news)
        bot.send_message(message.chat.id, text, parse_mode="Markdown", disable_web_page_preview=True)
    else:
        bot.send_message(message.chat.id, "❌ Новини недоступні. Спробуйте пізніше.")
    bot.send_message(message.chat.id, "💛 Підтримай бота!", reply_markup=donate_keyboard())

@bot.message_handler(func=lambda m: m.text == "🚨 Підписатись на тривоги")
def subscribe_alarms(message):
    subscribers = load_alarm_subscribers()
    chat_id = message.chat.id
    if chat_id not in subscribers:
        subscribers.append(chat_id)
        save_alarm_subscribers(subscribers)
        bot.reply_to(message, "🚨 Ти підписався на сповіщення про повітряні тривоги по всій Україні!")
    else:
        bot.reply_to(message, "ℹ️ Ти вже підписаний на тривоги!")

@bot.message_handler(func=lambda m: m.text == "🔕 Відписатись від тривог")
def unsubscribe_alarms(message):
    subscribers = load_alarm_subscribers()
    chat_id = message.chat.id
    if chat_id in subscribers:
        subscribers.remove(chat_id)
        save_alarm_subscribers(subscribers)
        bot.reply_to(message, "🔕 Ти відписався від сповіщень про тривоги.")
    else:
        bot.reply_to(message, "ℹ️ Ти не був підписаний на тривоги.")

@bot.message_handler(func=lambda m: m.text == "✅ Підписатись на новини")
def subscribe(message):
    subscribers = load_subscribers()
    chat_id = message.chat.id
    if chat_id not in subscribers:
        subscribers.append(chat_id)
        save_subscribers(subscribers)
        bot.reply_to(message, "✅ Ти підписався на щоранкові новини о 7:00!")
    else:
        bot.reply_to(message, "ℹ️ Ти вже підписаний!")

@bot.message_handler(func=lambda m: m.text == "❌ Відписатись від новин")
def unsubscribe(message):
    subscribers = load_subscribers()
    chat_id = message.chat.id
    if chat_id in subscribers:
        subscribers.remove(chat_id)
        save_subscribers(subscribers)
        bot.reply_to(message, "❌ Ти відписався від щоранкових новин.")
    else:
        bot.reply_to(message, "ℹ️ Ти не був підписаний.")

@bot.message_handler(func=lambda m: m.text == "🗺️ Карта тривог")
def alerts_map(message):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🗺️ Відкрити карту тривог", url=ALERTS_MAP))
    bot.send_message(message.chat.id, "🚨 Карта повітряних тривог України в реальному часі:", reply_markup=keyboard)

@bot.message_handler(func=lambda m: m.text == "📤 Поділитись ботом")
def share_bot(message):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("📤 Поділитись ботом", url=f"https://t.me/share/url?url={BOT_LINK}&text=Бот%20військових%20новин%20України%20🇺🇦"))
    bot.send_message(message.chat.id, f"📤 Поділись ботом з друзями!\n\n👉 {BOT_LINK}", reply_markup=keyboard)

@bot.message_handler(func=lambda m: m.text == "💛 Підтримати бота")
def donate(message):
    bot.send_message(message.chat.id, "💛 Дякую за підтримку! Кожна гривня допомагає розвивати бота 🇺🇦", reply_markup=donate_keyboard())

if __name__ == "__main__":
    print("Бот військових новин запущений...")
    thread = threading.Thread(target=send_morning_news)
    thread.daemon = True
    thread.start()
    alarm_thread = threading.Thread(target=check_alerts)
    alarm_thread.daemon = True
    alarm_thread.start()
    bot.infinity_polling()
