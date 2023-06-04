"""A module to handle requests used by B0BBA"""

import aiohttp


class Client:
    """Client class for the HTTP handler"""

    def __init__(self, **kwargs) -> None:
        self.headers = kwargs.get("headers", {})
        self.session = None

    async def get_session(self):
        """A method used internally by the http handler to get and cache the session

        Returns:
            ClientSession: AIOHTTP Clent session
        """
        if not self.session:
            self.session = aiohttp.ClientSession(headers=self.headers)

        return self.session

    async def get(self, url, **kwargs):
        """Create a GET request

        Args:
            url (str): The URL

        Returns:
            dict: JSON response
        """
        session = await self.get_session()

        async with session.get(url, **kwargs) as response:
            response.raise_for_status()
            return await response.json(content_type=None)

    async def post(self, url, **kwargs):
        """Create a POST request

        Args:
            url (str): The URL

        Returns:
            dict: JSON Response
        """
        session = await self.get_session()

        async with session.post(url, **kwargs) as response:
            response.raise_for_status()
            return await response.json(content_type=None)
