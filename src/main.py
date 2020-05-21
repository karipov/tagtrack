import re
import logging

from telethon import TelegramClient, events
from telethon.utils import get_peer_id
from telethon.tl.types import MessageEntityHashtag

from config import CONFIG
from ui import REPLIES
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

TAG_TO_BOARD = {
    '#bug': CONFIG['B&V']['bugs'],
    '#visual': CONFIG['B&V']['visual'],
    '#feature': CONFIG['FRQ']['requests'],
    '#suggestion': CONFIG['FRQ']['requests']
}


def check_tags():
    """
    Returns a filter function that checks if a certain tag is in a new event
    """
    return lambda event: any([tag in [
        text for _, text in event.get_entities_text(MessageEntityHashtag)
    ] for tag in CONFIG['TAGS']])


def escape_markdown(unescaped: str) -> str:
    """
    Utility function to escape markdown.
    """
    to_escape = ['*', '~', '>', '[', ']', '(', ')', '`', '=', '#', '-', '.']
    escaped, chars = [], list(unescaped)

    for char in chars:
        if char in to_escape:
            escaped.append('\\' + char)
        else:
            escaped.append(char)

    return ''.join(escaped)


@bot.on(events.NewMessage(func=check_tags(), chats=CONFIG['CHATS']))
async def process(event):
    first_tag = [text for _, text in event.get_entities_text()][0]

    try:
        version = re.search(r'[\d+\.]+ \(\d+\) Beta', event.raw_text).group(0)
    except AttributeError:  # if version not found
        version = REPLIES['VER_NA']

    text = event.text.replace(first_tag, '').replace(version, '')

    chat_id = get_peer_id(event.to_id, add_mark=False)
    card_name = text[:30] + '...'
    card_desc = REPLIES['DESC'].format(
        escape_markdown(text), version
    )

    response = await trello.new_card(
        list_id=TAG_TO_BOARD[first_tag],
        name=card_name,
        desc=card_desc,
        url_source=f'https://t.me/c/{chat_id}/{event.id}'
    )

    logging.warn(response)

    await event.reply(
        response['shortUrl']
    )


@bot.on(events.NewMessage(
    func=lambda e: e.is_reply, pattern=r'fix', from_users=CONFIG['DEVS']
))
async def fix(event):
    logging.warn("fixed issue")


bot.run_until_disconnected()
