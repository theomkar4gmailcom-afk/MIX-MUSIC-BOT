
import asyncio
from collections import defaultdict

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pytgcalls import PyTgCalls
from pytgcalls.types import AudioPiped

from config import API_ID, API_HASH, BOT_TOKEN, SESSION_STRING

# Telegram Bot
bot = Client(
    "music_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Assistant Account
assistant = Client(
    "assistant",
    api_id=36782950
    api_hash=608266c1128508c4503e3e3b08f526a5,
    session_string=BQCZzqEAhwkpkv0N3pclDnVkbw6EPawVOY9_3MZcLjT8r3Tamdeph0y1obkrd8BR9PGPpEfYW8bdE9VLveqh4rlsSfFt68IKJ9NmmT6T4wyqLjYsv4ZLLj1N38ys4pTSMuPkg0CDn_00OVKgIcDC424vhdmbWNtosNEYdlOfKTFjDKh8-uMAOcJcPnA585z0PYtBeu3vOcYwAeMw7525yaOMLlaFtyxrCQyMFGb0RLONnNuvAMuX3JC6n9fwmVK6O7F_vDOEQ3V8n41XK7G7A8dsE3YKlEhb2lCxW-sKplscoxKH7vhCMKYyVv37IycvWpAN5Bd5QOctBlMLsEIS1gx2rNuQNQAAAAIM1uqnAA
)

calls = PyTgCalls(assistant)

queues = defaultdict(list)
playing = set()


async def play_next(chat_id):
    if not queues[chat_id]:
        if chat_id in playing:
            try:
                await calls.leave_group_call(chat_id)
            except Exception:
                pass
            playing.discard(chat_id)
        return

    url = queues[chat_id].pop(0)

    try:
        if chat_id in playing:
            await calls.change_stream(
                chat_id, AudioPiped(url)
            )
        else:
            await calls.join_group_call(
                chat_id, AudioPiped(url)
            )
            playing.add(chat_id)

    except Exception as error:
        await bot.send_message(
            chat_id, f"Music Error: {error}"
        )
        await play_next(chat_id)


@bot.on_message(filters.command("start"))
async def start(_, message):
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "Help", callback_data="help"
            ),
            InlineKeyboardButton(
                "Support", url="https://t.me/"
            )
        ]
    ])

    await message.reply_text(
        "🎵 Welcome to Music Bot!\n\n"
        "Use /play to play music.\n"
        "Use /help for commands.",
        reply_markup=buttons
    )


@bot.on_callback_query(filters.regex("^help$"))
async def help_button(_, query):
    await query.answer()
    await query.message.reply_text(
        "/play AUDIO_URL\n"
        "/pause\n"
        "/resume\n"
        "/skip\n"
        "/stop\n"
        "/queue"
    )


@bot.on_message(filters.command("help"))
async def help_command(_, message):
    await message.reply_text(
        "🎵 MUSIC COMMANDS\n\n"
        "/play AUDIO_URL - Play\n"
        "/pause - Pause\n"
        "/resume - Resume\n"
        "/skip - Skip\n"
        "/stop - Stop\n"
        "/queue - Queue"
    )


@bot.on_message(filters.command("play"))
async def play_command(_, message):
    if len(message.command) < 2:
        return await message.reply_text(
            "Usage: /play AUDIO_URL"
        )

    url = message.text.split(maxsplit=1)[1].strip()

    if not url.startswith(("http://", "https://")):
        return await message.reply_text(
            "Please provide a valid audio URL."
        )

    chat_id = message.chat.id

    queues[chat_id].append(url)

    await message.reply_text("🎵 Added to queue!")

    if chat_id not in playing:
        await play_next(chat_id)


@bot.on_message(filters.command("pause"))
async def pause_command(_, message):
    try:
        await calls.pause_stream(message.chat.id)
        await message.reply_text("⏸ Music Paused!")
    except Exception as error:
        await message.reply_text(f"Error: {error}")


@bot.on_message(filters.command("resume"))
async def resume_command(_, message):
    try:
        await calls.resume_stream(message.chat.id)
        await message.reply_text("▶️ Music Resumed!")
    except Exception as error:
        await message.reply_text(f"Error: {error}")


@bot.on_message(filters.command("skip"))
async def skip_command(_, message):
    chat_id = message.chat.id

    if chat_id not in playing:
        return await message.reply_text(
            "Nothing is playing!"
        )

    await message.reply_text("⏭ Skipping...")
    await play_next(chat_id)


@bot.on_message(filters.command("stop"))
async def stop_command(_, message):
    chat_id = message.chat.id

    queues[chat_id].clear()

    if chat_id in playing:
        try:
            await calls.leave_group_call(chat_id)
        except Exception:
            pass

        playing.discard(chat_id)

    await message.reply_text("⏹ Music Stopped!")


@bot.on_message(filters.command("queue"))
async def queue_command(_, message):
    chat_id = message.chat.id
    items = queues[chat_id]

    if not items:
        return await message.reply_text(
            "Queue is empty!"
        )

    text = "🎶 MUSIC QUEUE\n\n"

    for i, url in enumerate(items, 1):
        text += f"{i}. {url}\n"

    await message.reply_text(text)


async def main():
    if not all([
        API_ID,
        API_HASH,
        BOT_TOKEN,
        SESSION_STRING
    ]):
        raise ValueError("Check your .env configuration!")

    await assistant.start()
    await bot.start()

    await calls.start()

    print("MUSIC BOT STARTED!")

    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
