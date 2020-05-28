import re

from telethon.tl.types import MessageEntityHashtag

from config import CONFIG
from ui import REPLIES


def extract_version(text: str):
    """
    Finds a semver telegram version from the text
    """
    try:
        version = re.search(r'[\d+\.]+ \(\d+\) Beta', text).group(0)
    except AttributeError:  # if version not found
        version = REPLIES['VER_NA']

    return version


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
