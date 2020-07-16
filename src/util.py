import re

from telethon.tl.types import MessageEntityHashtag
from telethon.utils import get_peer_id

from config import CONFIG
from ui import REPLIES

def dev_action(text: str) -> str:
    """
    Developer action types
    """
    if CONFIG["WORDS"]["reported"] in text.lower():
        return 'reported'

    if CONFIG["WORDS"]["fixed"] in text.lower():
        return 'fixed'
    
    if CONFIG["WORDS"]["rejected"] in text.lower():
        return 'rejected'

    return 'none'


def extract_version(text: str):
    """
    Finds a semver telegram version from the text
    """
    try:
        version = re.search(r'[\d+\.]+ \(\d+\)', text).group(0)
    except AttributeError:  # if version not found
        version = None

    return version


def extract_first_tag(message) -> str:
    """
    Assumes the tag exists.
    """
    return [
        text for _, text in message.get_entities_text(MessageEntityHashtag)
    ][0]


def extract_card_info(message) -> dict:
    """
    Extracts all the info needed for creating a card from a message
    """
    version = extract_version(message.raw_text)
    first_tag = extract_first_tag(message)
    text = message.raw_text.replace(first_tag, '').replace(version, '').strip()
    chat_id = get_peer_id(message.chat_id, add_mark=False)

    all_info = {
        'list_id': CONFIG['BOARD']['new'],
        'name': text[:40] + '...',
        'desc': REPLIES['DESC'].format(
            escape_markdown(text), version
        ),
        'url_source': f'https://t.me/c/{chat_id}/{message.id}'
    }

    label = CONFIG['LABELS'].get(first_tag)

    if label:
        all_info['label_id'] = label


def check_tags(message):
    """
    Returns a function that checks if a certain tag is in a new message
    """
    return any([tag in [
        text for _, text in message.get_entities_text(MessageEntityHashtag)
    ] for tag in CONFIG['TAGS']])


def check_media(message):
    """
    Checks whether a message is eligible to have its attached media uploaded
    to a trello card
    """
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
