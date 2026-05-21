# -*- coding: utf-8 -*-
import os
import telebot
import feedparser
from datetime import datetime

BOT_TOKEN = os.environ.get("BOT_TOKEN")

bot = telebot.TeleBot(BOT_TOKEN)

# RSS джерела військових новин
SOURCES = {
    "Генштаб ЗСУ": "https://www.mil.gov.ua/rss.xml",
    "Мілітарний": "https://militarny.com/feed/",
    "Українська правда (війна)": "https://www.pravda.com.ua/rss/view_war/",
}

def get_news(url, count=5):
    try:
        feed = feedparser.parse(url)
        news = []
        for entry in feed.entries[:count]:
            title = entry.get("title", "Без назви")
            link = entry.get("link", "")
            news.append(f"📰 {title}\n🔗 {link}")
        return news
    except Exception as e:
        return [f"Помилка отримання новин: {e}"]

@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    text = (
        "👋 Привіт! Я бот військових новин України.\n\n"
        "📋 Команди:\n"
        "/news — останні новини з усіх джерел\n"
        "/genshtab — зведення Генштабу ЗСУ\n"
        "/militarny — новини Мілітарного\n"
        "/pravda — Українська правда (війна)\n"
    )
    bot.reply_to(message, text)

@bot.message_handler(commands=["news"])
def all_news(message):
    bot.reply_to(message, "⏳ Збираю новини...")
    for source, url in SOURCES.items():
        news = get_news(url, 3)
        text = f"📡 *{source}*:\n\n" + "\n\n".join(news)
        bot.send_message(message.chat.id, text, parse_mode="Markdown", disable_web_page_preview=True)

@bot.message_handler(commands=["genshtab"])
def genshtab_news(message):
    bot.reply_to(message, "⏳ Завантажую зведення Генштабу...")
    news = get_news(SOURCES["Генштаб ЗСУ"], 5)
    text = "🪖 *Генштаб ЗСУ*:\n\n" + "\n\n".join(news)
    bot.send_message(message.chat.id, text, parse_mode="Markdown", disable_web_page_preview=True)

@bot.message_handler(commands=["militarny"])
def militarny_news(message):
    bot.reply_to(message, "⏳ Завантажую новини Мілітарного...")
    news = get_news(SOURCES["Мілітарний"], 5)
    text = "⚔️ *Мілітарний*:\n\n" + "\n\n".join(news)
    bot.send_message(message.chat.id, text, parse_mode="Markdown", disable_web_page_preview=True)

@bot.message_handler(commands=["pravda"])
def pravda_news(message):
    bot.reply_to(message, "⏳ Завантажую новини УП...")
    news = get_news(SOURCES["Українська правда (війна)"], 5)
    text = "📰 *Українська правда (війна)*:\n\n" + "\n\n".join(news)
    bot.send_message(message.chat.id, text, parse_mode="Markdown", disable_web_page_preview=True)

if __name__ == "__main__":
    print("Бот військових новин запущений...")
    bot.infinity_polling()
