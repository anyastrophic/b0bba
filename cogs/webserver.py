"""The webserver module of B0BBA"""

import secrets
import asyncio
import os

import json
import discord
import git

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from pydantic import BaseModel  # pylint: disable=no-name-in-module

from discord.ext import commands

from modules.database_utils import Registration

request_queue = {}

app = FastAPI()

API_KEY = os.environ.get("B0BBA_API_KEY")

BOT = None

print("hi")


class Server(BaseModel):
    """Server data sent from ROBLOX"""

    age: float | int | None
    players: dict | list
    fps: float | int | None


class VerificationRequest(BaseModel):
    """Verification request sent from ROBLOX"""

    roblox_id: str
    discord_id: str


class Webserver(commands.Cog, name="webserver"):
    """The class containing the webserver functions"""

    def __init__(self, _bot):
        global BOT  # pylint: disable=global-statement

        self.bot = _bot

        if _bot is not None:
            BOT = _bot


async def create_request(_type: str, job_id: str = "global"):
    """Creates request

    Args:
        t (str): The request type
        job_id (str, optional): The job id. Defaults to "global".

    Returns:
        JSONResponse: The response
    """
    request_id = secrets.token_hex(16)

    def callback(response: dict):
        request_queue[request_id]["response"] = JSONResponse(content=response)

    request_queue[request_id] = {"callback": callback, "response": None}

    await BOT.roblox_universe.publish_message(
        "global",
        json.dumps(
            {
                "request_id": request_id,
                "job_id": job_id,
                "type": _type,
            }
        ),
    )

    async def wait_for_response():
        timeout = 10

        while True:
            if request_queue[request_id]["response"] is not None:
                return request_queue[request_id]["response"]

            await asyncio.sleep(0.1)
            timeout -= 0.1
            if timeout <= 0:
                return JSONResponse(content={"message": "Timeout"}, status_code=418)

    return await wait_for_response()


@app.get("/servers/{job_id}")
async def get_server_info(job_id: str):
    """Gets info about a UB server

    Args:
        job_id (str): The job id

    Returns:
        JSONResponse: The response
    """
    return await create_request("get_server_info", job_id=job_id)


@app.post("/respond/{request_id}")
async def respond(request_id: str, server_data: Server):
    """Function that gets called when ROBLOX responds to a request created by B0BBA

    Args:
        request_id (str): The request id
        server_data (Server): The server's data
    """
    request_queue[request_id]["callback"](server_data.__dict__)


@app.get("/")
async def read_root():
    """Function that gets called when user visits the root of the API

    Returns:
        int: always returns 200
    """
    return 200


@app.post(f"/{API_KEY}")
async def github_webhook():
    """Github webhook endpoint, currently used to restart the bot on Push"""
    _git = git.cmd.Git(".")
    _git.pull()

    os.startfile("main.py")

    pid = os.getpid()
    os.system(f"taskkill /F /PID {pid}")


@app.post("/verify")
async def verify_endpoint(request: Request, verification_request: VerificationRequest):
    """Verifies user specified in the verification request

    Args:
        request (Request): The request
        verification_request (VerificationRequest): The verification request

    Returns:
        JSONResponse: The response
    """
    headers = request.headers

    roblox_id = int(verification_request.roblox_id)
    discord_id = int(verification_request.discord_id)
    api_key = headers.get("api-key")

    if api_key is None:
        return JSONResponse(
            content={"message": "Missing header api-key"}, status_code=400
        )

    if api_key != API_KEY:
        return JSONResponse(content={"message": "Invalid API key"}, status_code=401)

    await Registration(discord_id, roblox_id).links()

    _ = (
        BOT.ub_guild.members
    )  # this is just to cache everyone, so the below doesn't return an error

    member: discord.Member = BOT.ub_guild.get_member(discord_id)
    role: discord.Role = BOT.ub_guild.get_role(406997457709432862)

    if role not in member.roles:
        await member.add_roles(role)

    return JSONResponse(content={"message": "OK"}, status_code=200)


async def setup(bot):
    """The setup function for the webserver module

    Args:
        bot (discord.Bot): The bot object
    """
    await bot.add_cog(Webserver(bot))
