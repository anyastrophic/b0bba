import aiohttp
import secrets
import os

from modules.get_setup import get_setup
from modules.b0bba_error import RobloxUtilsError
from modules.placeholders import Placeholder

API_KEY = os.environ.get('ROBLOX_API_KEY')
COOKIE = os.environ.get('ROBLOX_COOKIE')

APIS = "https://apis.roblox.com"

async def get_csrf():
    async with aiohttp.ClientSession(headers = {"Cookie": f'.ROBLOSECURITY={COOKIE}'}) as session:
        async with session.post("https://auth.roblox.com") as response:
            return response.headers.get("x-csrf-token")

class Request():
    def __init__(self) -> None:
        pass

    async def check_status(self, response):
        pass
        # if response.status == 429:
        #     raise(RobloxUtilsError("Too many requests!"))
        # if response.status != 200:
        #     print(response)
        #     raise(RobloxUtilsError(Placeholder.Errors.RobloxUtils.BadResponse))

    async def get(self, url, **kwargs):
        async with aiohttp.ClientSession(headers = kwargs.get("headers", {})) as session:
            async with session.get(url, json = kwargs.get("json", {})) as response:
                await self.check_status(response)
                return {"response": response, "json": await response.json(content_type = None)}

    async def post(self, url, **kwargs):
        async with aiohttp.ClientSession(headers = kwargs.get("headers", {})) as session:
            async with session.post(url, json = kwargs.get("json", {})) as response:
                await self.check_status(response)
                return {"response": response, "json": await response.json(content_type = None)}
            
class User():
    def __init__(self, id: int) -> None:
        self.id = id

    async def get_data(self):
        result = await Request().get(f"https://users.roblox.com/v1/users/{self.id}")

        json = result['json']
        
        return json
    
    async def get_headshot(self, **kwargs):
        result = await Request().get(f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={self.id}&size={kwargs.get('size', '720x720')}&format={kwargs.get('format', 'png')}&isCircular={kwargs.get('circle', 'false')}")

        return result['json']['data'][0]['imageUrl']

    async def get_username(self):
        result = await self.get_data()
        return result['name']
    
    async def get_id_from_username(self, username, limit = False):
        result = await Request().post("https://users.roblox.com/v1/usernames/users", json = {
            "usernames": [
                username
            ],
            "excludeBannedUsers": True
        })

        if len(result['json']['data']) > 0 and limit:
             return result['json']['data']
        elif len(result['json']['data']) > 0 and not limit:
            return result['json']['data'][0]['id']
        else:
            raise(RobloxUtilsError(Placeholder.Errors.RobloxUtils.UsernameNotFound))
        
class Place():
    def __init__(self, id: int) -> None:
        self.id = id
    
    async def get_servers(self):
        result = await Request().get(f"https://games.roblox.com/v1/games/{self.id}/servers/Public?sortOrder=Asc&limit=100")
        
        return result

class Universe():
    def __init__(self, id: int):
        self.id = id

    async def publish_message(self, topic, message):
        result = await Request().post(f"{APIS}/messaging-service/v1/universes/{self.id}/topics/{topic}", headers = {"x-api-key": API_KEY}, json = {"message": message})
        
        return result
    
    async def update_data(self, datastore, key, value):
        if type(key) == 'str' and key.isnumeric(): key = int(key)

        result = await Request().post(f"{APIS}/datastores/v1/universes/{self.id}/standard-datastores/datastore/entries/entry?datastoreName={datastore}&entryKey={key}", headers = {
            "x-api-key": API_KEY,
            "content-type": "application/json",
        }, json = value)

        return result
    
class Group():
    def __init__(self, id: int) -> None:
        self.id = id

    async def get_user_role(self, user_id: int):
        result = await Request().get(f"https://groups.roblox.com/v2/users/{user_id}/groups/roles")
        data = None

        for item in result['json']["data"]:
            if item['group']['id'] == self.id:
                data = item
                break

        if data:
            return data['role']
        else:
            return {
                "id": 0,
                "name": "Guest",
                "rank": 0
            }