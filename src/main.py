import logging
from pathlib import Path

from telethon import TelegramClient, events
import colorlog

from config import CONFIG
from models import Tags
import trello
import util


# LOGGING SETUP
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = colorlog.ColoredFormatter(
    '%(log_color)s%(asctime)s - %(name)s - %(message)s'
)

console = logging.StreamHandler()
console.setLevel(logging.INFO)

debug_file = logging.FileHandler(Path.cwd().joinpath(CONFIG['LOG']['DEBUG']))
debug_file.setLevel(logging.DEBUG)

info_file = logging.FileHandler(Path.cwd().joinpath(CONFIG['LOG']['INFO']))
info_file.setLevel(logging.INFO)

handlers = [console, debug_file, info_file]

[x.setFormatter(formatter) for x in handlers]
[logger.addHandler(x) for x in handlers]


# OBJECTS SETUP
bot = TelegramClient(
    CONFIG['BOT_SESSION'],
    CONFIG['TG_API_ID'],
    CONFIG['TG_API_HASH']
).start(bot_token=CONFIG['BOT_TOKEN'])

boards = trello.TrelloAPI()


# HANDLERS SETUP
@bot.on(events.Album(chats=CONFIG['CHATS']))
async def album_process(event):
    msg_caption = None

    for message in event.messages:
        if not util.check_tags(message):
            continue
        else:
            msg_caption = message
            break

    if not msg_caption:
        return

    response = await boards.new_card(**util.extract_card_info(msg_caption))

    Tags(
        chat_id=event.chat_id,
        message_id=msg_caption.id,
        user_id=event.from_user.id,
        card_id=response['id'],
        short_url=response['shortUrl']
    ).save()

    for message in event.messages:
        if not util.check_media(message):
            return

        stream = await message.download_media(file=bytes)

        await boards.attach_card(
            response['id'],
            stream,
            str(message.id) + message.file.ext,
            message.file.mime_type
        )


@bot.on(events.NewMessage(
    func=lambda e: util.check_tags(e) and not e.grouped_id,
    chats=CONFIG['CHATS']
))
async def process(event):
    response = await boards.new_card(**util.extract_card_info(event))

    Tags(
        chat_id=event.chat_id,
        message_id=event.id,
        user_id=event.from_user.id,
        card_id=response['id'],
        short_url=response['shortUrl']
    ).save()

    if not util.check_media(event):
        return

    logger.info(
        f"{event.from_user.id} uploaded a new issue {response['shortUrl']}"
    )

    stream = await event.download_media(file=bytes)

    await boards.attach_card(
        response['id'],
        stream,
        str(event.id) + event.file.ext,
        event.file.mime_type
    )


@bot.on(events.NewMessage(
    func=lambda e: e.is_reply, pattern=r'fix', from_users=CONFIG['DEVS']
))
async def fix(event):
    try:
        tag = Tags.get(
            Tags.chat_id == event.chat_id,
            Tags.message_id == event.reply_to_msg_id
        )
    except Exception:
        return

    logger.info(f"{event.from_user.id} fixed issue {tag.short_url}")

    first_tag = [text for _, text in (
        await event.get_reply_message()
    ).get_entities_text()][0]

    await boards.move_card(tag.card_id, util.TAG_TO_BOARD_FIX[first_tag])


# RUN THE BOT ON POLLING
bot.run_until_disconnected()
