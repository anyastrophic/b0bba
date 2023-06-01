import secrets
import asyncio
import json
import os
import discord
import random
import git 

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

from pydantic import BaseModel

from discord.ext import commands

from modules.database_utils import Registration

chunk = None

request_queue = {}

app = FastAPI()

API_KEY = os.environ.get('B0BBA_API_KEY')

bot = None

class Webserver(commands.Cog, name = "webserver"):
    def __init__(self, _bot):
        global bot
        
        self.bot = _bot
        
        bot = _bot

async def start_stream():
    global _chunk

    dir = os.listdir(r"\\KEENETIC\Seagate Basic\Stuff\Music\\")
    while True:
        random.shuffle(dir)
    
        for file in dir:
            if file.endswith(".mp3"):
                with open(rf"\\KEENETIC\Seagate Basic\Stuff\Music\{file}", "rb") as f:
                    for chunk in iter(lambda: f.read(3056), b''):
                        await current_chunk.set_value(chunk)

                        await asyncio.sleep(0.13)

@app.on_event("startup")
async def startup_event():
    asyncio.Task(start_stream())

async def create_request(t: str, job_id: str = 'global'):
    request_id = secrets.token_hex(16)

    def callback(response: dict):
        request_queue[request_id]['response'] = JSONResponse(content = response)

    request_queue[request_id] = {"callback": callback, "response": None}

    await bot.roblox_universe.publish_message("global", json.dumps({
        "request_id": request_id,
        "job_id": job_id,
        "type": t,
    }))

    async def wait_for_response():
        timeout = 10

        while True:

            if request_queue[request_id]['response'] != None:
                return request_queue[request_id]['response']
            
            await asyncio.sleep(0.1)
            timeout -= 0.1
            if timeout <= 0:
                return JSONResponse(content = {"message": "Timeout"}, status_code = 418)

    return await wait_for_response()

class Server(BaseModel):
    age: float | int | None
    players: dict | list
    fps: float | int | None

class Subscription():
    def __init__(self, callback) -> None:
        self.callback = callback

    async def call(self):
        await self.callback()

class Watcher():
    def __init__(self) -> None:
        self.subscriptions = []
        self.value = 0
    
    async def subscribe(self, callback):
        self.subscriptions.append(Subscription(callback))

    async def set_value(self, value):
        self.value = value

        for subscription in self.subscriptions:
            await subscription.call()

    def get_value(self):
        return self.value

current_chunk = Watcher()

stream_started = False
@app.get("/stream")
async def stream_endpoint():
    async def stream():

        old_chunk = 0

        while True:
            await asyncio.sleep(0.0)

            if old_chunk != current_chunk.get_value():
                old_chunk = current_chunk.get_value()

                yield old_chunk

    return StreamingResponse(stream(), media_type = 'audio/mp3', headers={'Content-Disposition': 'inline; filename="Anya\'s Improvised Radio"'})

@app.get("/servers/{job_id}")
async def get_server_info(job_id: str):
    return await create_request('get_server_info', job_id = job_id)
    
@app.post("/respond/{request_id}")
async def respond(request_id: str, server_data: Server):
    request_queue[request_id]['callback'](server_data.__dict__)

@app.get("/")
async def read_root(request: Request):
    return 200
    return await stream_endpoint(request)

@app.post("/TA2SnLcQYHmcNos4ipXb5CYsrUZb58bRo6FEN3tjzFxFTnuMQLJB1jtQpQmlWp1I")
async def github_webhook():
    g = git.cmd.Git('.')
    g.pull()

    os.startfile("main.py")
    
    pid = os.getpid()
    os.system(f'taskkill /F /PID {pid}')
    
class VerificationRequest(BaseModel):
    roblox_id: str
    discord_id: str
    
@app.post("/verify")
async def verify_endpoint(request: Request, verification_request: VerificationRequest):
    headers = request.headers
    
    roblox_id = int(verification_request.roblox_id)
    discord_id = int(verification_request.discord_id)
    api_key = headers.get('api-key')

    if api_key is None:
        return JSONResponse(content = {"message": "Missing header api-key"}, status_code = 400)
    
    if api_key != API_KEY:
        return JSONResponse(content = {"message": "Invalid API key"}, status_code = 401)
    
    await Registration(discord_id, roblox_id).links()
   
    member: discord.Member = bot.ub_guild.get_member(discord_id)
    role: discord.Role = bot.ub_guild.get_role(406997457709432862)
    
    if not role in member.roles:
        await member.add_roles(role)
    
    return JSONResponse(content = {"message": "OK"}, status_code = 200)

async def setup(bot):
    await bot.add_cog(Webserver(bot))