import aiohttp

from config import CONFIG


BASE_URL = "https://api.trello.com/1"
BASE_PARAMS = {
    'key': CONFIG['TRELLO_API_KEY'],
    'token': CONFIG['TRELLO_API_TOKEN']
}


# async def get_boards(session, url: str, params: dict):
#     async with session.get(
#         f"{url}/boards/{CONFIG['FRQ']['_id']}/lists", params=params
#     ) as resp:
#         return await resp.json()


async def new_card(list_id: str, message):
    name, desc = message.text[:20] + '...', message.text
    params = {
        'name': name,
        'desc': desc,
        'pos': 'top',
        'idList': list_id,
    }
    params.update(BASE_PARAMS)

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BASE_URL}/cards", params=params) as resp:
            return await resp.json()
