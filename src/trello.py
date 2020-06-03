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

class TrelloAPI:
    def __init__(self):
        self.session = aiohttp.ClientSession()

    async def new_card(
        self,
        list_id: str,
        name: str,
        desc: str,
        url_source: str
    ):
        """
        Creates a new trello card
        """
        params = {
            'name': name,
            'desc': desc,
            'pos': 'top',
            'idList': list_id,
            'urlSource': url_source
        }
        params.update(BASE_PARAMS)

        async with self.session.post(f"{BASE_URL}/cards", params=params) as r:
            return await r.json()

    async def move_card(self, card_id: str, to_list_id: str):
        params = {
            'idList': to_list_id
        }
        params.update(BASE_PARAMS)

        await self.session.put(
            f"{BASE_URL}/cards/{card_id}", params=params
        )

    async def attach_card(self, card_id: str, file_bytes, file_name, mime):
        data = {'file': file_bytes}
        headers = {"Accept": "application/json"}
        params = {'name': file_name, 'mimeType': mime}
        params.update(BASE_PARAMS)

        await self.session.post(
            f"{BASE_URL}/cards/{card_id}/attachments",
            params=params,
            data=data,
            headers=headers
        )
