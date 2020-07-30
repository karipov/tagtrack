import re
import logging

from telethon.tl.types import MessageEntityHashtag
from telethon.utils import get_peer_id

from config import CONFIG


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def dev_action(text: str) -> str:
    """
    Developer action types
    """
    if CONFIG["WORDS"]["reported"] in text.lower():
        return 'reported'

    if CONFIG["WORDS"]["fixed"] in text.lower():
        return 'fixed'

    if CONFIG["WORDS"]["reject"] in text.lower():
        return 'reject'

    if CONFIG["WORDS"]["create"] in text.lower():
        return 'create'

    if CONFIG["WORDS"]["delete"] in text.lower():
        return 'delete'

    return False


def extract_version(text: str) -> bool:
    """
    Finds a semver telegram version from the text
    """
    try:
        # searches for: "x.x.x (XXXX)" or "x.x.x XXXXX"
        version = re.search(
            r'([\d\.]+\s{0,}\(\d+\)|[\d\.]+\s{0,}\d+)', text
        ).group(0)
    except AttributeError:  # if version not found
        version = False

    device = any([x in text.lower() for x in [
        'iphone', 'ipad', 'ipod', 'se'
    ]])
    software = any([
        'ios' in text.lower(),
        re.search(r'(?:[8-9]|1[0-5]).[0-7]', text)  # ios version perhaps
    ])

    return bool(version and device and software)


def extract_tags(message, first=True) -> str:
    """
    Assumes the tag exists.
    """
    all_tags = [
        text for _, text in message.get_entities_text(MessageEntityHashtag)
    ]

    if first:
        return all_tags[0]
    else:
        return all_tags


def extract_link(message) -> str:
    """
    Generates a link for a message
    """
    chat_id = get_peer_id(message.chat_id, add_mark=False)
    return f'https://t.me/c/{chat_id}/{message.id}'


def extract_card_info(message) -> dict:
    """
    Extracts all the info needed for creating a card from a message
    """
    all_tags = extract_tags(message, first=False)
    title_text = message.raw_text.replace('\n', ' ').strip()

    for tag in all_tags:
        title_text = title_text.replace(tag, '').strip()

    title_text = title_text[:40] + '...'

    all_info = {
        'list_id': CONFIG['BOARD']['new'],
        'name': title_text,
        'desc': escape_markdown(message.raw_text),
        'url_source': extract_link(message)
    }

    label = None
    for tag in all_tags:
        label = CONFIG['LABELS'].get(tag)
        if label:
            all_info['label_id'] = label
            break

    return all_info


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


def extract_extension(message) -> str:
    ext = message.file.ext

    if ext == '.jpe':
        ext = '.jpeg'

    return ext


# BOT HTTP API IS RESTRICTED FOR THIS TO MATTER

# def is_album(event) -> str:
#     """
#     Is event part of an album?
#     """
#     if event.grouped_id:
#         return True

#     return False


# async def build_album(event) -> list:
#     """
#     Trie to builds an album from a single message event
#     """
#     AFTER, BEFORE = event.id + 7, event.id - 7

#     messages = await event.client.get_messages(
#         event.chat_id, min_id=BEFORE, max_id=AFTER
#     )
#     album_messages = [x for x in messages if x.grouped_id]

#     # pseudo album class
#     album = event
#     setattr(album, 'messages', album_messages)

#     return album
