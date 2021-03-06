import aiohttp

from config import CONFIG


BASE_URL = "https://api.trello.com/1"
BASE_PARAMS = {
    'key': CONFIG['TRELLO_API_KEY'],
    'token': CONFIG['TRELLO_API_TOKEN']
}


class TrelloAPI:
    def __init__(self):
        self.session = aiohttp.ClientSession()

    async def _get_boards(self):
        async with self.session.get(
           f"{BASE_URL}/members/me/boards", params=BASE_PARAMS
        ) as r:
            return await r.json()

    async def _get_lists(self, board_id: str) -> dict:
        params = {}
        params.update(BASE_PARAMS)

        async with self.session.get(
            f"{BASE_URL}/boards/{board_id}/lists", params=params
        ) as r:
            return await r.json()

    async def _get_labels(self, board_id: str) -> dict:
        async with self.session.get(
            f"{BASE_URL}/boards/{board_id}/labels", params=BASE_PARAMS
        ) as r:
            return await r.json()

    async def new_card(
        self,
        list_id: str,
        name: str,
        desc: str,
        url_source: str,
        label_id: str = None
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

        if label_id:
            params['idLabels'] = label_id

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
        data = aiohttp.FormData()
        data.add_field(
            'file', file_bytes, filename=file_name, content_type=mime
        )

        headers = {"Accept": "application/json"}
        params = {'name': file_name, 'mimeType': mime}
        params.update(BASE_PARAMS)

        await self.session.post(
            f"{BASE_URL}/cards/{card_id}/attachments",
            params=params,
            data=data,
            headers=headers
        )

    async def label_card(self, card_id: str, label_id: str):
        params = {'value': label_id}
        params.update(BASE_PARAMS)

        await self.session.post(
            f"{BASE_URL}/cards/{card_id}/idLabels",
            params=params
        )

    async def archive_card(self, card_id: str):
        params = {'closed': True}
        params.update(BASE_PARAMS)

        await self.session.put(
            f"{BASE_URL}/cards/{card_id}",
            params=params
        )

    async def delete_card(self, card_id: str):
        await self.session.delete(
            f"{BASE_URL}/cards/{card_id}",
            params=BASE_PARAMS
        )

    async def comment_card(self, text: str, card_id: str):
        params = {
            'text': text
        }
        params.update(BASE_PARAMS)

        await self.session.post(
            f"{BASE_URL}/cards/{card_id}/actions/comments",
            params=params
        )


if __name__ == "__main__":
    from pprint import pprint as print
    import asyncio

    async def main():
        trello = TrelloAPI()
        print(await trello._get_lists("5edad38f47346048774a9fcf"))

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
