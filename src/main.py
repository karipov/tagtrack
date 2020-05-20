from telethon import TelegramClient, events
from telethon.tl.types import MessageEntityHashtag

from config import CONFIG
import trello

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


@bot.on(events.NewMessage(func=check_tags(), chats=CONFIG['CHATS']))
async def process(event):
    first_tag = [text for _, text in event.get_entities_text()][0]

    response = await trello.new_card(
        list_id=TAG_TO_BOARD[first_tag],
        message=event
    )

    await event.reply(response['shortUrl'])


bot.run_until_disconnected()
