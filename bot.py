import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN env var is not set")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

waiting_queue = []
partners = {}
states = {}

def reset_user(user_id: int):
    states[user_id] = "idle"
    partners.pop(user_id, None)
    try:
        waiting_queue.remove(user_id)
    except ValueError:
        pass

def connect_users(a: int, b: int):
    partners[a] = b
    partners[b] = a
    states[a] = "chatting"
    states[b] = "chatting"

@dp.message(Command("start"))
async def cmd_start(message: Message):
    reset_user(message.from_user.id)
    await message.answer(
        "Привет! Я аноним‑чат бот.\n"
        "/find — найти собеседника\n"
        "/stop — завершить чат\n"
        "/help — помощь"
    )

@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer("Нажмите /find, чтобы найти собеседника. /stop — завершить чат.")

@dp.message(Command("find"))
async def cmd_find(message: Message):
    uid = message.from_user.id
    st = states.get(uid, "idle")

    if st == "chatting":
        await message.answer("Вы уже в чате. /stop — чтобы завершить.")
        return
    if st == "waiting":
        await message.answer("Вы уже в поиске. Подождите немного.")
        return

    if waiting_queue:
        other = waiting_queue.pop(0)
        connect_users(uid, other)
        await message.answer("Собеседник найден. Пишите сообщение.")
        await bot.send_message(other, "Вас подключили. Пишите сообщение.")
    else:
        waiting_queue.append(uid)
        states[uid] = "waiting"
        await message.answer("Ищу собеседника... Подключу, как только появится кто‑то ещё.")

@dp.message(Command("stop"))
async def cmd_stop(message: Message):
    uid = message.from_user.id
    pid = partners.get(uid)

    if pid:
        partners.pop(pid, None)
        partners.pop(uid, None)
        states[pid] = "idle"
        states[uid] = "idle"
        await message.answer("Диалог завершён. /find — чтобы начать заново.")
        await bot.send_message(pid, "Собеседник завершил диалог. /find — чтобы найти нового.")
        return

    if states.get(uid) == "waiting":
        try:
            waiting_queue.remove(uid)
        except ValueError:
            pass
        states[uid] = "idle"
        await message.answer("Поиск остановлен.")
    else:
        await message.answer("Вы сейчас ни с кем не общаетесь.")

@dp.message(F.content_type.in_({"text","photo","document","audio","voice","video","video_note","sticker"}))
async def relay(message: Message):
    uid = message.from_user.id
    pid = partners.get(uid)
    if not pid:
        await message.answer("Вы ни с кем не общаетесь. Нажмите /find.")
        return

    if message.text:
        await bot.send_message(pid, f"Собеседник: {message.text}")
        return
    if message.photo:
        await bot.send_photo(pid, message.photo[-1].file_id, caption="Фото от собеседника"); return
    if message.document:
        await bot.send_document(pid, message.document.file_id, caption="Документ от собеседника"); return
    if message.voice:
        await bot.send_voice(pid, message.voice.file_id, caption="Голосовое от собеседника"); return
    if message.audio:
        await bot.send_audio(pid, message.audio.file_id, caption="Аудио от собеседника"); return
    if message.video:
        await bot.send_video(pid, message.video.file_id, caption="Видео от собеседника"); return
    if message.video_note:
        await bot.send_video_note(pid, message.video_note.file_id); return
    if message.sticker:
        await bot.send_sticker(pid, message.sticker.file_id); return

async def main():
    print("Bot started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
