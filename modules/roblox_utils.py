import os

from aiohttp import ClientResponseError

COOKIE = os.environ.get("ROBLOX_COOKIE")


async def get_csrf(client):
    try:
        await client.post(
            "https://auth.roblox.com",
            headers={"Cookie": f".ROBLOSECURITY={COOKIE}"},
        )
    except ClientResponseError as exc:
        headers = exc.headers
        csrf_token = headers.get("x-csrf-token")

        assert csrf_token is not None, "csrf token is None"

        return csrf_token
