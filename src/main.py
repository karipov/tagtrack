import logging
from pathlib import Path

from telethon import TelegramClient, events
import colorlog

from config import CONFIG
from ui import REPLIES
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

    if not util.extract_version(msg_caption.raw_text):
        await event.reply(REPLIES['INCLUDE_VER'])
        return

    logging.info(util.extract_card_info(msg_caption))
    response = await boards.new_card(**util.extract_card_info(msg_caption))
    reply = await event.reply(
        REPLIES['ACCEPTED'].format(REPLIES['ISSUE_STATUS']['new']),
        parse_mode='HTML'
    )

    # every single message in album is considered as an issue for purposes
    # of ensuring that an admin reply to any of them triggers a dev action
    # if appropriate.
    data_source = list()
    for message in event.messages:
        data_source.append({
            "chat_id": event.chat_id,
            "message_id": message.id,
            "reply_message_id": reply.id,
            "user_id": event.sender.id,
            "card_id": response['id'],
            "short_url": response['shortUrl']
        })
    Tags.insert_many(data_source).execute()  # bulk insert for speed

    logging.info(
        f"{event.sender.id} uploaded a new issue {response['shortUrl']} "
        + "with Photo Album"
    )

    for message in event.messages:

        if not util.check_media(message):
            continue

        stream = await message.download_media(file=bytes)

        await boards.attach_card(
            response['id'],
            stream,
            str(message.id) + util.extract_extension(message),
            message.file.mime_type
        )


@bot.on(events.NewMessage(
    func=lambda e: util.check_tags(e) and not e.grouped_id,  # disregard album
    chats=CONFIG['CHATS']
))
async def process(event):
    if not util.extract_version(event.raw_text):
        await event.reply(REPLIES['INCLUDE_VER'])
        return

    response = await boards.new_card(**util.extract_card_info(event))
    reply = await event.reply(
        REPLIES['ACCEPTED'].format(REPLIES['ISSUE_STATUS']['new']),
        parse_mode='HTML'
    )

    Tags.create(
        chat_id=event.chat_id,
        message_id=event.id,
        reply_message_id=reply.id,
        user_id=event.sender.id,
        card_id=response['id'],
        short_url=response['shortUrl']
    )

    logging.info(
        f"{event.sender.id} uploaded a new issue {response['shortUrl']}"
    )

    if not util.check_media(event):
        return

    stream = await event.download_media(file=bytes)

    await boards.attach_card(
        response['id'],
        stream,
        str(event.id) + util.extract_extension(event),
        event.file.mime_type
    )


@bot.on(events.NewMessage(
    func=lambda e: e.is_reply,
    from_users=CONFIG['ADMINS'],
    chats=CONFIG['CHATS']
))
async def admin_action(event):
    try:
        tag = Tags.get(
            Tags.chat_id == event.chat_id,
            Tags.message_id == event.reply_to_msg_id
        )
    except Exception as e:
        logging.warning(f"not triggered {e}")
        return  # if it's just a normal reply

    action = util.dev_action(event.raw_text)

    logging.info(f"{event.sender.id} responded to issue {tag.short_url}")

    if not action:
        return

    list_id = CONFIG['BOARD'][action]

    await event.client.edit_message(
        tag.chat_id,
        tag.reply_message_id,
        REPLIES['ACCEPTED'].format(REPLIES['ISSUE_STATUS'][action]),
        parse_mode='HTML'
    )
    await boards.move_card(tag.card_id, list_id)


# RUN THE BOT ON POLLING
bot.run_until_disconnected()
