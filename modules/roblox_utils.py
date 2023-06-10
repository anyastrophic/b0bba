import os

COOKIE = os.environ.get("ROBLOX_COOKIE")


async def get_csrf(client):
    result = await client.post(
        "https://auth.roblox.com",
        headers={"Cookie": f".ROBLOSECURITY={COOKIE}"},
    )

    json = result.json.as_dict()

    csrf_token = json.get("x-csrf-token")

    assert csrf_token is not None, "csrf token is None"

    return csrf_token
