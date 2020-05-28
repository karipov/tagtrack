import logging

from telethon import TelegramClient, events
from telethon.utils import get_peer_id

from config import CONFIG
from ui import REPLIES
from util import check_tags, escape_markdown, extract_version
from models import Tags
import trello


logging.basicConfig(
    format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
    level=logging.WARNING
)

bot = TelegramClient(
    CONFIG['BOT_SESSION'],
    CONFIG['TG_API_ID'],
    CONFIG['TG_API_HASH']
).start(bot_token=CONFIG['BOT_TOKEN'])

boards = trello.TrelloAPI()

TAG_TO_BOARD = {
    '#bug': CONFIG['B&V']['bugs'],
    '#visual': CONFIG['B&V']['visual'],
    '#feature': CONFIG['FRQ']['requests'],
    '#suggestion': CONFIG['FRQ']['requests']
}

TAG_TO_BOARD_FIX = {
    '#bug': CONFIG['B&V']['completed'],
    '#visual': CONFIG['B&V']['completed'],
    '#feature': CONFIG['FRQ']['completed'],
    '#suggestion': CONFIG['FRQ']['completed']
}


@bot.on(events.Album(chats=CONFIG['CHATS']))
async def album_process(event):
    for message in event.messages:
        if not check_tags()(message):
            continue
        else:
            msg_caption = message
            break

    version = extract_version(msg_caption.raw_text)
    first_tag = [text for _, text in msg_caption.get_entities_text()][0]
    text = msg_caption.text.replace(first_tag, '').replace(version, '').strip()
    chat_id = get_peer_id(event.to_id, add_mark=False)

    response = await boards.new_card(
        list_id=TAG_TO_BOARD[first_tag],
        name=text[:30] + '...',
        desc=REPLIES['DESC'].format(escape_markdown(text), version),
        url_source=f'https://t.me/c/{chat_id}/{event.id}'
    )

    bot_reply = await event.reply(
        REPLIES['LINK'].format(response['shortUrl'])
    )

    Tags.create(
        chat_id=event.chat_id,
        message_id=event.id,
        reply_message_id=bot_reply.id,
        card_id=response['id'],
        short_url=response['shortUrl']
    )


@bot.on(events.NewMessage(func=check_tags(), chats=CONFIG['CHATS']))
async def process(event):
    version = extract_version(event.raw_text)
    first_tag = [text for _, text in event.get_entities_text()][0]
    text = event.text.replace(first_tag, '').replace(version, '').strip()
    chat_id = get_peer_id(event.to_id, add_mark=False)

    response = await boards.new_card(
        list_id=TAG_TO_BOARD[first_tag],
        name=text[:30] + '...',
        desc=REPLIES['DESC'].format(
            escape_markdown(text), version
        ),
        url_source=f'https://t.me/c/{chat_id}/{event.id}'
    )

    bot_reply = await event.reply(
        REPLIES['LINK'].format(response['shortUrl'])
    )

    if event.media:
        _ = event.client.iter_download(event.media)

    Tags.create(
        chat_id=event.chat_id,
        message_id=event.id,
        reply_message_id=bot_reply.id,
        card_id=response['id'],
        short_url=response['shortUrl']
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

    first_tag = [text for _, text in (
        await event.get_reply_message()
    ).get_entities_text()][0]

    await event.client.edit_message(
        tag.chat_id,
        tag.reply_message_id,
        REPLIES['LINK_FIX'].format(tag.short_url)
    )

    await boards.move_card(tag.card_id, TAG_TO_BOARD_FIX[first_tag])


# RUN THE BOT ON POLLING
bot.run_until_disconnected()
