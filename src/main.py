import logging
from pathlib import Path

from telethon import TelegramClient, events, errors
import colorlog

from config import CONFIG
from ui import REPLIES
from models import Storage, Tags
import trello
import util


# LOGGING SETUP
logger = logging.getLogger()  # getting the root logger
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


# USER MESSAGES AND ERROR REPORTS (SINGLE MESSAGE)
@bot.on(events.Album(
    chats=CONFIG['CHATS']  # tag checking occurs in-function
))
async def album_process(event):
    message_with_caption = None
    album_ids = list()

    for message in event.messages:
        album_ids.append(message.id)
        if not util.check_tags(message):
            continue
        else:
            message_with_caption = message
            break

    if not message_with_caption:
        return

    storage_info = {
        "chat_id": event.chat_id,
        "message_id": message_with_caption.id,
        "album_ids": album_ids,
        "user_id": event.sender.id,
        "valid": False
    }

    if not util.extract_version(message_with_caption.raw_text):

        logging.info(
            f"User {event.sender.id}: "
            "missing version info to create card for Photo Album"
            + util.extract_link(event)
        )

        reply = await event.reply(REPLIES['INCLUDE_VER'])
        storage_info['reply_message_id'] = reply.id
        Storage.insert(storage_info)
        return

    response = await boards.new_card(**util.extract_card_info(
        message_with_caption
    ))

    reply = await event.reply(
        REPLIES['ACCEPTED'].format(
            response['shortUrl'].replace('https://trello.com/c/', ''),
            REPLIES['ISSUE_STATUS']['new']
        ),
        parse_mode='HTML'
    )

    storage_info.update({
        'reply_message_id': reply.id,
        'card_id': response['id'],
        'short_url': response['shortUrl'],
        'valid': True
    })
    Storage.insert(storage_info)

    logger.info(
        f"User {event.sender.id} triggered a new issue {response['shortUrl']} "
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


# USER MESSAGES AND ERROR REPORTS (SINGLE MESSAGE)
@bot.on(events.NewMessage(
    func=lambda e: util.check_tags(e) and not e.grouped_id,  # disregard album
    chats=CONFIG['CHATS']
))
async def process(event):
    storage_info = {
        "chat_id": event.chat_id,
        "message_id": event.id,
        "album_ids": [event.id],
        "user_id": event.sender.id,
        "valid": False
    }

    if not util.extract_version(event.raw_text):

        logging.info(
            f"User {event.sender.id}: "
            "missing version info to create card for message "
            + util.extract_link(event)
        )

        reply = await event.reply(REPLIES['INCLUDE_VER'])
        storage_info['reply_message_id'] = reply.id
        Storage.insert(storage_info)
        return

    response = await boards.new_card(**util.extract_card_info(event))
    reply = await event.reply(
        REPLIES['ACCEPTED'].format(
            response['shortUrl'].replace('https://trello.com/c/', ''),
            REPLIES['ISSUE_STATUS']['new']
        ),
        parse_mode='HTML'
    )

    storage_info.update({
        'reply_message_id': reply.id,
        'card_id': response['id'],
        'short_url': response['shortUrl'],
        'valid': True
    })
    Storage.insert(storage_info)

    logger.info(
        f"User {event.sender.id} uploaded a new issue {response['shortUrl']}"
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


# ADMIN ACTIONS AND REPLIES
@bot.on(events.NewMessage(
    func=lambda e: e.is_reply,
    from_users=CONFIG['ADMINS'],
    chats=CONFIG['CHATS']
))
async def admin_action(event):
    action = util.dev_action(event.raw_text)

    try:
        tag = Storage.search(
            (Tags.chat_id == event.chat_id)
            & (Tags.album_ids.any([event.reply_to_msg_id]))
            & (Tags.valid == True)  # noqa: E712
        )[0]
    except IndexError:
        if action == 'create':
            candidate_message = await event.get_reply_message()
            link_to_candidate_message = util.extract_link(candidate_message)

            try:
                logger.info(
                    f"Admin {event.sender.id} manually triggered card "
                    + "creation for message "
                    + link_to_candidate_message
                )

                await process(candidate_message)
            except Exception:
                logging.warn(
                    f"Admin {event.sender.id}: "
                    + "not enough information to create card for message "
                    + link_to_candidate_message
                )
        return

    logger.info(
        f"Admin {event.sender.id} responded to issue {tag['short_url']} "
        + f"with action: {action}"
    )

    if not action or action == 'create':
        return

    if action == 'delete':
        await boards.delete_card(card_id=tag['card_id'])
        await event.client.delete_messages(
            event.chat_id, tag['reply_message_id']
        )
        Storage.remove(doc_ids=[tag.doc_id])
        return

    list_id = CONFIG['BOARD'][action]

    try:
        await event.client.edit_message(
            tag['chat_id'],
            tag['reply_message_id'],
            REPLIES['ACCEPTED'].format(
                tag['short_url'].replace('https://trello.com/c/', ''),
                REPLIES['ISSUE_STATUS'][action]
            ),
            parse_mode='HTML'
        )
    except errors.MessageNotModifiedError:
        pass

    # if the command consists of a payload
    if event.raw_text.replace('#' + action, '').strip():
        await boards.comment_card(
            REPLIES['COMMENT_TRELLO'].format(
                event.sender.first_name,
                util.extract_link(event),
                event.raw_text
            ),
            tag['card_id']
        )

    await boards.move_card(tag['card_id'], list_id)


# EDITED USER MESSAGES
@bot.on(events.MessageEdited(
    # only care about edited messages with neccessary tags and text
    func=lambda e: util.check_tags(e),
    chats=CONFIG['CHATS']
))
async def edited_process(event):
    link_to_event = util.extract_link(event)
    base_log = f"User {event.sender.id} edited message {link_to_event} "

    try:
        tag = Storage.search(
            (Tags.chat_id == event.chat_id)
            & (Tags.message_id == event.id)
        )[0]
    except IndexError:
        # if the proper tag wasn't used:
        # if util.is_album(event):
        #     album = await util.build_album(event)
        #     logging.info("built album")
        #     await album_process(album)
        # else:
        logger.info(
            f"{base_log} triggered card creation for message {link_to_event}"
        )
        await process(event)
        return

    if tag['valid']:
        # everything ok we don't touch it...
        # https://t.me/c/1168424726/192
        logger.info(
            f"{base_log} which is already a valid issue {tag['short_url']}"
        )
        return

    if not util.extract_version(event.raw_text):
        logger.info(
            f"{base_log} which is still missing version info."
        )
        return

    response = await boards.new_card(**util.extract_card_info(event))
    await event.client.edit_message(
        tag['chat_id'],
        tag['reply_message_id'],
        REPLIES['ACCEPTED'].format(
            response['shortUrl'].replace('https://trello.com/c/', ''),
            REPLIES['ISSUE_STATUS']['new']
        ),
        parse_mode='HTML'
    )

    logger.info(
        f"{base_log} which passed all validation and created a trello card "
        + response['shortUrl']
    )

    # event though message fetching is impossible
    # we at least upload and attach this media.
    if util.check_media(event):
        stream = await event.download_media(file=bytes)
        await boards.attach_card(
            response['id'],
            stream,
            str(event.id) + util.extract_extension(event),
            event.file.mime_type
        )

    Storage.update({
        'card_id': response['id'],
        'short_url': response['shortUrl'],
        'valid': True
    }, doc_ids=[tag.doc_id])


# RUN THE BOT ON POLLING
bot.run_until_disconnected()
