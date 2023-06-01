import motor
import motor.motor_asyncio

import time

import asyncio

import random
import secrets
import discord
import roblox.users

client = motor.motor_asyncio.AsyncIOMotorClient('mongodb://localhost:27017')
client.get_io_loop = asyncio.get_running_loop
db = client['b0bba']

class Registration():
    def __init__(self, discord_id: int, roblox_id: int = None) -> None:
        self.discord_id = discord_id
        self.roblox_id = roblox_id
    
    async def check_registration(self, collection: str) -> bool:
        return await db[collection].find_one({"discord_id": self.discord_id})

    async def economy(self) -> None:
        registration = await self.check_registration("economy")
        if registration:
            if (registration["luck_addend"] == 0) or (registration['luck_addend'] > 1) or (registration['luck_addend'] < -5):
                await db["economy"].update_one({"discord_id": self.discord_id}, {"$set": {"luck_addend": random.uniform(1.0, -5.0)}})

            if not "stocks" in registration:
                await db["economy"].update_one({"discord_id": self.discord_id}, {"$set": {"stocks": {}}})

            return registration
        
        await db["economy"].insert_one({
            "discord_id": self.discord_id,

            "copies": 0,
            "deletes": 0,

            "inventory": {}, # item: amount
            "reputation": 50.0,
            "luck_addend": random.uniform(1.0, -5.0),
            "stocks": {}
        })

        return await self.economy()

    async def blacklist(self, reason: str = "Data deletion") -> None: # register user in blacklist collection (lol)
        if await self.check_registration("blacklist"): return

        await db["blacklist"].insert_one({
            "reason": reason,
            "discord_id": self.discord_id
        })

    async def links(self):
        assert self.roblox_id, "No Roblox ID specified"

        if await db["links"].find_one({"discord_id": self.discord_id}) or await db["links"].find_one({"roblox_id": self.roblox_id}): return

        await db["links"].insert_one({
            "discord_id": self.discord_id,
            "roblox_id": self.roblox_id
        })

    async def admins(self):
        if await db["admins"].find_one({"discord_id": self.discord_id}): return

        await db["admins"].insert_one({
            "discord_id": self.discord_id,

            "payout": 0,
            "payouts_received": {},

            "reports_closed": {},
        })

    async def economy_marketplace(self, item: str, stock: int, price_per_item: int):
        if await db["economy_marketplace"].find_one({"discord_id": self.discord_id}): return

        listing_id = secrets.token_hex(4)

        await db["economy_marketplace"].insert_one({
            "owner": {
                "discord_id": self.discord_id,
            },
            "item": item,
            "price_per_item": price_per_item,
            "stock": stock,
            "listing_id": listing_id
        })

        return listing_id
    
    async def reports(
        self, 
        report_id: int, 
        report_description: str, 
        closed_by: discord.User, 
        report_creator: discord.User,
        reported_user: roblox.users.User
    ):
        if await db['reports'].find_one({"report_id": report_id}): return
        
        await db['reports'].insert_one({
            "report_id": report_id, # snowflake id of the post
            "report_description": report_description, # Content of the message
            
            "report_metadata":{
                "created_at": time.time(), # unix timestamp
                "closed_by": {
                    "discord_id": closed_by.id, # snowflake id
                    "discord_username": f'{closed_by.name}#{closed_by.discriminator}' # username, such as anyastrophic#2775 or @anyastrophic
                }
            },
            
            "report_creator":{
                "discord_id": report_creator.id, # snowflake id
                "discord_username": f'{report_creator.name}#{report_creator.discriminator}',
            },
            "reported_user":{
                "roblox_id": reported_user.id, # duh
                "roblox_username": reported_user.name,
            }
        })


async def check_link(discord_id: int):
    return await db['links'].find_one({'discord_id': discord_id})

async def delete_data(discord_id: int): # data deletion, called when a user requests data deletion, to comply with GDPR
    collections = [name for name in await db.list_collection_names()]

    for collection in collections:
        if collection == 'admins':
            continue
        
        await db[collection].delete_one({'discord_id': discord_id})

    await Registration.blacklist(discord_id)

async def get_marketplace_listings(discord_id: int = None):
    economy_marketplace = db.economy_marketplace

    listings = []

    if discord_id is not None:
        async for document in economy_marketplace.find({'owner.discord_id': discord_id, 'stock': {'$gt': 0}}): # find all listings, which aren't closed (stock > 0)
            listings.append(document)
    else:
        async for document in economy_marketplace.find({'stock': {'$gt': 0}}): # find all listings, which aren't closed (stock > 0)
            listings.append(document)

    return listings