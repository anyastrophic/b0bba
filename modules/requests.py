from .exceptions import HttpException  # pylint:disable=relative-beyond-top-level
import aiohttp


class Request:
    def __init__(self) -> None:
        pass

    async def check_status(self, response):
        if response.status == 429:
            raise (
                HttpException(
                    f"Too many requests, response: {response}", response.status
                )
            )
        if response.status == 401:
            raise (
                HttpException(f"Unauthorized, response: {response}", response.status)
            )
        if response.status == 400:
            raise (HttpException(f"Bad request, response: {response}", response.status))

    async def get(self, url, **kwargs):
        async with aiohttp.ClientSession(headers=kwargs.get("headers", {})) as session:
            async with session.get(
                url, json=kwargs.get("json", {}), params=kwargs.get("params", {})
            ) as response:
                await self.check_status(response)
                return await response.json(content_type=None)

    async def post(self, url, **kwargs):
        async with aiohttp.ClientSession(headers=kwargs.get("headers", {})) as session:
            async with session.post(
                url, json=kwargs.get("json", {}), params=kwargs.get("params", {})
            ) as response:
                await self.check_status(response)
                return await response.json(content_type=None)
