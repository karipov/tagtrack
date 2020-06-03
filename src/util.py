import re

from telethon.tl.types import MessageEntityHashtag
from telethon.utils import get_peer_id

from config import CONFIG
from ui import REPLIES


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


def extract_version(text: str):
    """
    Finds a semver telegram version from the text
    """
    try:
        version = re.search(r'[\d+\.]+ \(\d+\) Beta', text).group(0)
    except AttributeError:  # if version not found
        version = REPLIES['VER_NA']

    return version


def extract_card_info(message) -> dict:
    version = extract_version(message.raw_text)
    first_tag = [
        text for _, text in message.get_entities_text(MessageEntityHashtag)
    ][0]
    text = message.text.replace(first_tag, '').replace(version, '').strip()
    chat_id = get_peer_id(message.chat_id, add_mark=False)

    return {
        'list_id': TAG_TO_BOARD[first_tag],
        'name': text[:30] + '...',
        'desc': REPLIES['DESC'].format(
            escape_markdown(text), version
        ),
        'url_source': f'https://t.me/c/{chat_id}/{message.id}'
    }


def check_tags(message):
    """
    Returns a filter function that checks if a certain tag is in a new message
    """
    return any([tag in [
        text for _, text in message.get_entities_text(MessageEntityHashtag)
    ] for tag in CONFIG['TAGS']])


def check_media(message):
    if not message.file:
        return False

    if message.file.size > 10 * 1024 * 1024:  # 10MB limit for Trello API
        return False

    return True


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
