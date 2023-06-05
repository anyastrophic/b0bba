"""A module to handle requests used by B0BBA"""

import types
import aiohttp


class Json:
    """An object representing the JSON of the response"""

    def __init__(self, json: dict) -> None:
        self.json = json

    def as_dict(self):
        """A method to return the JSON as a python dictionary

        Returns:
            dict: The JSON
        """
        return self.json

    def as_object(self):
        """A method to return the JSON as a python object

        Returns:
            object: The JSON
        """
        return types.SimpleNamespace(**self.json)


class Response:
    """A response class containing `ClientResponse` from aiohttp, JSON body and headers"""

    def __init__(self, response: aiohttp.ClientResponse, json: dict) -> None:
        self.response: aiohttp.ClientResponse = response
        self.headers: dict = response.headers
        self.json: Json = Json(json)


class Client:
    """Client class for the HTTP handler"""

    def __init__(self, **kwargs) -> None:
        self.headers = kwargs.get("headers", {})
        self.session = None

    async def get_session(self) -> aiohttp.ClientSession:
        """A method used internally by the http handler to get and cache the session

        Returns:
            ClientSession: AIOHTTP Clent session
        """
        if not self.session:
            self.session = aiohttp.ClientSession(headers=self.headers)

        return self.session

    async def get(self, url: str, **kwargs) -> Response:
        """Create a GET request

        Args:
            url (str): The URL

        Returns:
            dict: JSON response
        """
        session = await self.get_session()

        async with session.get(url, **kwargs) as response:
            response.raise_for_status()
            return Response(response, await response.json())

    async def post(self, url: str, **kwargs) -> Response:
        """Create a POST request

        Args:
            url (str): The URL

        Returns:
            dict: JSON Response
        """
        session = await self.get_session()

        async with session.post(url, **kwargs) as response:
            response.raise_for_status()
            return Response(response, await response.json())
