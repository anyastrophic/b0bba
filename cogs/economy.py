"""The economy module of B0BBA"""

import random

from typing import List

import discord

from discord import app_commands
from discord.ext import commands, tasks

from modules.economy_utils import (
    probably,
    get_stock_info,
    get_rarity,
)
from modules.database_utils import (
    Registration,
    get_marketplace_listings,
)

from modules.enums import Enum
from modules.loggers import Logger

exchange_values = {"TempleCoin": {"deletes": 1337, "copies": 1337}}

ZERO_WIDTH_SPACE = "\u200B"

ITEMS = {
    "TempleCoin": "The bot's currency",
    "Server Ban Pass": "ServerBan a user, making them lose all their copies and deletes",
    "Luck Resetter": "Reset your luck",
    "Build Token": "Build something without waiting for the cooldown!",
    "Grief Token": "Grief something without waiting for the cooldown!",
    "Lucky Amulet": "An amulet in the shape of a temple, which boosts your luck (boost stackable)",
}

RARITIES = {
    "common": ["Build Token", "Grief Token"],  # 50%
    "uncommon": [],  # 37.5%
    "rare": ["TempleCoin"],  # 28.1%
    "very rare": ["Server Ban Pass"],  # 21%
    "epic": [],  # 15.8%
    "legendary": ["Luck Resetter"],  # 11.8%
    "mythic": [],  # 8.8%
    "limited": ["Lucky Amulet"],  # 0%
}


async def get_item_rarity(item: str) -> str:
    for rarity in RARITIES:
        if item in RARITIES[rarity]:
            return rarity


async def update_exchange_rates(bot):
    """
    :param discord.Bot bot: bot class
    """
    total_templecoins = 0

    result = bot.db.economy.find({}, {})
    _list = await result.to_list(100)

    for document in _list:
        if "TempleCoin" in document["inventory"]:
            total_templecoins += document["inventory"]["TempleCoin"]

    copies_price = round(500 / (1 + (total_templecoins * 0.00001)))
    deletes_price = copies_price / 2

    if copies_price < 200:
        copies_price = 200
        deletes_price = copies_price / 2

    if round(exchange_values["TempleCoin"]["copies"]) != round(copies_price):
        Logger.Economy.Misc.ExchangeRatesUpdated(copies_price, deletes_price)

    exchange_values["TempleCoin"] = {"copies": copies_price, "deletes": deletes_price}


class Economy(commands.Cog, name="economy"):
    """Economy module"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """A function that's called upon the Economy module starting up"""
        self.update_exchange.start()  # pylint: disable=no-member

    @tasks.loop(seconds=30.0)
    async def update_exchange(self):
        """Update exchange rates (task)"""
        await update_exchange_rates(self.bot)

    item_commands = app_commands.Group(name="item", description="Commands for items")

    @item_commands.command(name="info", description="Get info about an item")
    async def _item_info(self, interaction: discord.Interaction, item: str) -> None:
        if item not in ITEMS:
            await interaction.response.send_message("This item doesn't exist!")

            return

        embed = discord.Embed(
            title=f"{item} info",
            description=ITEMS[item],
            colour=Enum.Embeds.Colors.Info,
        )

        item_rarity = await get_item_rarity(item)

        embed.add_field(name="Rarity", value=f"`{item_rarity.upper()}`")

        await interaction.response.send_message(embed=embed)

    @_item_info.autocomplete("item")
    async def _use_items_autocomplete(
        self, _: discord.Interaction, current: str
    ) -> List[app_commands.Choice[str]]:
        item_list = ITEMS
        return [
            app_commands.Choice(name=item, value=item)
            for item in item_list
            if current.lower() in item.lower()
        ]

    stocks_commands = app_commands.Group(
        name="stocks", description="Commands for stocks"
    )

    @stocks_commands.command()
    @commands.guild_only()
    async def info(self, interaction: discord.Interaction, stock: str):
        """get info about a stock"""

        stock_info = None

        try:
            stock_info = await get_stock_info(stock)
        except:  # pylint: disable=bare-except  # noqa: E722
            await interaction.response.send_message(
                "Unable to find stock! Are you entering the name correctly?"
            )

            return

        await interaction.response.send_message(
            f"{stock}\n**Price**: `{stock_info['meta']['regularMarketPrice']} TempleCoins`"
        )

    @stocks_commands.command(name="buy")
    @commands.guild_only()
    async def stocks_buy(
        self, interaction: discord.Interaction, stock: str, amount: int = 1
    ):
        """buy a stock"""
        registration = await Registration(interaction.user.id).economy()

        stock_info = None

        try:
            stock_info = await get_stock_info(stock)
        except Exception:  # pylint: disable=broad-exception-caught
            await interaction.response.send_message(
                "Unable to find stock! Are you entering the name correctly?"
            )

            return

        stock_price = stock_info["meta"]["regularMarketPrice"]

        if stock_price * amount < 1:
            await interaction.response.send_message(
                "This stock is too cheap, you can't buy it"
            )

            return

        if registration["inventory"].get("TempleCoin", 0) >= stock_price * amount:
            await self.bot.db.economy.update_one(
                {"discord_id": interaction.user.id},
                {
                    "$inc": {
                        "inventory.TempleCoin": -(stock_price * amount),
                        f"stocks.{stock}": amount,
                    }
                },
            )

            await interaction.response.send_message(
                f"You successfully purchased `{amount}` `{stock}` for `{stock_price * amount} TempleCoins`!"
            )
        else:
            await interaction.response.send_message(
                "You don't have enough TempleCoins for this transaction!"
            )

    @stocks_commands.command(name="sell")
    @commands.guild_only()
    async def stock_sell(
        self, interaction: discord.Interaction, stock: str, amount: int = 1
    ):
        """sell a stock"""

        if amount < 1:
            return

        registration = await Registration(interaction.user.id).economy()

        stock_info = None

        try:
            stock_info = await get_stock_info(stock)
        except:  # pylint: disable=bare-except
            await interaction.response.send_message(
                "Unable to find stock! Are you entering the name correctly?"
            )

            return

        stock_price = stock_info["meta"]["regularMarketPrice"]

        if registration["stocks"].get(stock, 0) >= amount:
            await self.bot.db.economy.update_one(
                {"discord_id": interaction.user.id},
                {
                    "$inc": {
                        "inventory.TempleCoin": amount * stock_price,
                        f"stocks.{stock}": -amount,
                    }
                },
            )

            await interaction.response.send_message(
                f"You successfully sold `{amount}` `{stock}` for `{stock_price * amount} TempleCoins`!"
            )

        else:
            await interaction.response.send_message(
                "You don't have enough of this stock for this transaction!"
            )

    @app_commands.command()
    @commands.guild_only()
    async def use(
        self,
        interaction: discord.Interaction,
        item: str,
        amount: int = 1,
        target: discord.User = None,
    ):
        """Use an item from your inventory"""

        registration = await Registration(interaction.user.id).economy()

        if registration["inventory"].get(item, 0) < amount:
            await interaction.response.send_message("You don't enough of this item!")

            return

        if target is not None:
            await Registration(target.id).economy()

        match item:
            case "Server Ban Pass":
                amount = 1  # normalize amount, you can only use one with this item

                if target is None:
                    await interaction.response.send_message(
                        "You haven't specified a target to use this item on!"
                    )

                    return

                await self.bot.db.economy.update_one(  # clear target's copies and deletes (use item)
                    {"discord_id": target.id}, {"$set": {"copies": 0, "deletes": 0}}
                )

                await interaction.response.send_message(
                    f"You successfully used `{item}` on `{target}`, causing them to lose all their copies and deletes!"
                )

            case "Luck Resetter":
                amount = 1  # normalize amount, you can only use one with this item

                await self.bot.db.economy.update_one(
                    {"discord_id": interaction.user.id},
                    {"$set": {"luck_addend": random.uniform(1.0, -5.0)}},
                )

                await interaction.response.send_message(
                    f"You successfully used `{item}` and your luck has been reset!"
                )

            case "Build Token":
                amount = 1  # normalize amount, you can only use one with this item

                build_command = self.bot.tree.get_command("build")
                await build_command.callback(self, interaction)

            case "Grief Token":
                amount = 1  # normalize amount, you can only use one with this item

                grief_command = self.bot.tree.get_command("grief")
                await grief_command.callback(self, interaction)

            case _:
                await interaction.response.send_message("This item cannot be used!")

                return

        await self.bot.db.economy.update_one(  # take item from user
            {"discord_id": interaction.user.id},
            {"$inc": {f"inventory.{item}": -amount}},
        )

    @use.autocomplete("item")
    async def _use_items_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> List[app_commands.Choice[str]]:
        registration = await Registration(interaction.user.id).economy()
        item_list = registration["inventory"]
        return [
            app_commands.Choice(name=item, value=item)
            for item in item_list
            if item_list[item] > 0
            and current.lower() in item.lower()
            and item != "TempleCoin"
        ]

    @app_commands.command()
    @commands.guild_only()
    async def stats(self, interaction: discord.Interaction, user: discord.User = None):
        """find out economy info about a user"""

        if user is None:
            user = interaction.user

        await Registration(user.id).economy()

        user_data = await self.bot.db.economy.find_one({"discord_id": user.id})

        embed = discord.Embed(title=f"{user}'s stats", colour=Enum.Embeds.Colors.Info)

        embed.add_field(
            name="Reputation", value=round(user_data["reputation"], 2), inline=False
        )

        embed.add_field(name="Copies", value=user_data["copies"], inline=False)

        embed.add_field(name="Deletes", value=user_data["deletes"], inline=False)

        inventory = ""
        for key, value in user_data["inventory"].items():
            if value != 0:
                if key == "TempleCoin":
                    value = round(value, 2)

                inventory = inventory + f"**{key}**: `{value}` | `{ITEMS[key]}`\n"

        stocks = ""
        for key, value in user_data["stocks"].items():
            if value > 0:
                stocks = stocks + f"**{key}**: `{value}`\n"

        embed.add_field(name="Inventory", value=inventory, inline=False)

        embed.add_field(name="Stocks", value=stocks, inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @commands.guild_only()
    @app_commands.checks.cooldown(1, 600)
    async def build(self, interaction: discord.Interaction):
        """build something!"""

        await interaction.response.defer()

        await Registration(interaction.user.id).economy()

        add_copies = random.randint(90, 300)
        add_deletes = round(add_copies / 3)
        add_reputation = 0.1

        choices = random.choices(["u", "b"], k=random.randint(10, 15))

        original_string = " ".join(choices)
        fake_string = f" {ZERO_WIDTH_SPACE * random.randint(2, 10)}".join(choices)

        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel

        await interaction.followup.send(
            f"Let's get building! Retype this: `{fake_string}`", ephemeral=False
        )

        msg = await self.bot.wait_for("message", check=check)

        if msg.content == fake_string:
            await msg.reply(
                "You did terrible by failing to copy someone else's build. You did not earn anything."
            )

            return

        if msg.content != original_string:
            await msg.reply("Your build sucks. You did not earn anything.")

            return

        if msg.content == original_string:
            registration = await Registration(interaction.user.id).economy()

            rarity = await get_rarity(
                registration["luck_addend"]
                + registration["inventory"].get("Lucky Amulet", 0)
            )
            add_item = None

            if rarity is not None:
                items_in_rarity = RARITIES[rarity]

                if len(items_in_rarity) > 0:
                    add_item = random.choice(items_in_rarity)

            if add_item:
                await msg.reply(
                    f"Good job! You built something and earnt `{add_copies} copies`, `{add_deletes} deletes` and `{add_reputation} reputation`!\nYou also found `1` `{rarity.upper()}` `{add_item}` while building!"
                )
                await self.bot.db.economy.update_one(
                    {"discord_id": interaction.user.id},
                    {"$inc": {f"inventory.{add_item}": 1}},
                )
            else:
                await msg.reply(
                    f"Good job! You built something and earnt `{add_copies} copies`, `{add_deletes} deletes` and `{add_reputation} reputation`!"
                )

        # last checks

        author_data = await self.bot.db.economy.find_one(
            {"discord_id": interaction.user.id}
        )

        if author_data["reputation"] + add_reputation > 100:
            add_reputation = 100 - author_data["reputation"]

        await self.bot.db.economy.update_one(
            {"discord_id": interaction.user.id},
            {
                "$inc": {
                    "copies": add_copies,
                    "deletes": add_deletes,
                    "reputation": add_reputation,
                }
            },
        )

    @app_commands.command()
    @commands.guild_only()
    async def coinflip(self, interaction: discord.Interaction, bet: int = 1):
        """flip a coin (must have at least one templecoin to gamble)"""

        if bet < 0:
            return

        registration = await Registration(interaction.user.id).economy()

        templecoins_to_give = bet / 2

        if registration["inventory"].get("TempleCoin", 0) >= bet:
            if probably(
                (
                    50
                    + registration["luck_addend"]
                    + registration["inventory"].get("Lucky Amulet", 0)
                )
                / 100
            ):
                await interaction.response.send_message(
                    f"You flipped a coin and **won**! You got {bet / 2} TempleCoins."
                )
            else:
                await interaction.response.send_message(
                    f"You flipped a coin and **lost**! You lost {bet} TempleCoins."
                )
                templecoins_to_give = -bet

            await self.bot.db.economy.update_one(
                {"discord_id": interaction.user.id},
                {"$inc": {"inventory.TempleCoin": templecoins_to_give}},
            )
        else:
            await interaction.response.send_message(
                "You don't have enough TempleCoins!", ephemeral=True
            )

    # @app_commands.command()
    # async def crash(self, ctx, bet: int = 1, cashout_at: float = 1.0):
    #     '''play a game of crash (goes up to 2x)'''

    #     if bet < 0: return
    #     if cashout_at < 0: return

    #     if cashout_at > 2:
    #         await interaction.response.send_message('You're cashing out too late! The maximum cashout number is 2')
    #         return

    #     registration = await Registration.economy(interaction.user.id)

    #     if not await TempleCoins.get_amount(registration['inventory']) > bet:
    #         await interaction.response.send_message('You don't have enough TempleCoins to play crash!')
    #         return

    #     multiplier = random.randint(0, 20) / 10
    #     current_multiplier = 0

    #     victory = False

    #     message = await interaction.response.send_message(f'Crash!\nThe current multiplier is: **{current_multiplier}**')

    #     while True:
    #         if round(current_multiplier, 2) == cashout_at:
    #             victory = True
    #             break

    #         if multiplier <= current_multiplier: break
    #         current_multiplier += 0.1

    #         await message.edit(content = f'Crash!\nThe current multiplier is: **{round(current_multiplier, 2)}**')
    #         await asyncio.sleep(0.7)

    #     if victory:
    #         await message.edit(content = f'Crash ended!\nThe multiplier went up to: **{multiplier}**\nYou **won** `{int(bet * cashout_at)} TempleCoins`!')
    #         await TempleCoins.add(registration['inventory'], int((bet * cashout_at) - bet))
    #     else:
    #         await message.edit(content = f'Crash ended!\nThe multiplier went up to: **{multiplier}**\nYou **lost** `{bet} TempleCoins`!')
    #         await TempleCoins.remove(registration['inventory'], bet)

    #     await self.bot.db.economy.update_one({'discord_id': interaction.user.id}, {'$set': {'inventory': registration['inventory']}})

    @app_commands.command()
    @commands.guild_only()
    @app_commands.checks.cooldown(1, 600)
    async def grief(self, interaction: discord.Interaction):
        """grief everyone!!!"""

        registration = await Registration(interaction.user.id).economy()

        add_deletes = random.randint(40, 80)
        dec_reputation = 0.2

        fail = probably(
            (
                25
                - registration["luck_addend"]
                - registration["inventory"].get("Lucky Amulet", 0)
            )
            / 100
        )
        if fail:
            add_deletes = 0

            await interaction.response.send_message(
                f"You've been caught by an admin and your deletes from this griefing session were undone! You also lost `{dec_reputation} reputation`"
            )
        else:
            await interaction.response.send_message(
                f"You griefed and earnt `{add_deletes} deletes`. You also lost `{dec_reputation} reputation`"
            )

        author_data = await self.bot.db.economy.find_one(
            {"discord_id": interaction.user.id}
        )
        if author_data["reputation"] - dec_reputation < 0:
            dec_reputation = 0

        await self.bot.db.economy.update_one(
            {"discord_id": interaction.user.id},
            {"$inc": {"deletes": add_deletes, "reputation": -dec_reputation}},
        )

    @app_commands.command()
    @commands.guild_only()
    @app_commands.checks.cooldown(1, 86400)
    async def report(self, interaction: discord.Interaction):
        """report a user for free reputation (economy)"""

        add_reputation = 1

        author_data = await self.bot.db.economy.find_one(
            {"discord_id": interaction.user.id}
        )

        if author_data["reputation"] + add_reputation > 100:
            add_reputation = 100 - author_data["reputation"]

        await self.bot.db.economy.update_one(
            {"discord_id": interaction.user.id},
            {"$inc": {"reputation": add_reputation}},
        )

        random_member = random.choice(interaction.guild.members)

        await interaction.response.send_message(
            f"You reported `{random_member.name}#{random_member.discriminator}` for `{random.choice(['Griefing', 'Trolling', 'Bullying'])}` and received `{round(add_reputation)} reputation`"
        )

    @app_commands.command()
    @commands.guild_only()
    @app_commands.checks.cooldown(1, 86400)
    async def falsereport(self, interaction: discord.Interaction):
        """false report a user for free reputation (has a chance of backfiring) (economy)"""

        registration = await Registration(interaction.user.id).economy()

        reputation = 1

        author_data = await self.bot.db.economy.find_one(
            {"discord_id": interaction.user.id}
        )

        random_member = random.choice(interaction.guild.members)

        if probably(
            (
                33
                - registration["luck_addend"]
                - registration["inventory"].get("Lucky Amulet", 0)
            )
            / 100
        ):
            if author_data["reputation"] - reputation < 0:
                reputation = 0

            await interaction.response.send_message(
                f"You got caught false reporting `{random_member.name}#{random_member.discriminator}` for `{random.choice(['Griefing', 'Trolling', 'Bullying'])}` and lost `{round(reputation)} reputation`"
            )

            await self.bot.db.economy.update_one(
                {"discord_id": interaction.user.id},
                {"$inc": {"reputation": -reputation}},
            )
        else:
            if author_data["reputation"] + reputation > 100:
                reputation = 100 - author_data["reputation"]

            await interaction.response.send_message(
                f"You false reported `{random_member.name}#{random_member.discriminator}` for `{random.choice(['Griefing', 'Trolling', 'Bullying'])}` and received `{round(reputation)} reputation`"
            )

            await self.bot.db.economy.update_one(
                {"discord_id": interaction.user.id},
                {"$inc": {"reputation": reputation}},
            )

    @app_commands.command()
    @commands.guild_only()
    async def give(
        self,
        interaction: discord.Interaction,
        user: discord.User,
        item: str,
        amount: int = 1,
    ):
        """sharing is caring!"""

        if user == interaction.user:
            await interaction.response.send_message("You can't give items to yourself!")
            return

        if amount < 0:
            return

        author_data = await Registration(interaction.user.id).economy()

        if item is None:
            await interaction.response.send_message(
                "You haven't specified what item you want to give!", ephemeral=True
            )

            return

        if author_data["inventory"].get(item, 0) < amount:
            await interaction.response.send_message(
                "You don't have this many of this item to give!", ephemeral=True
            )

            return

        await self.bot.db.economy.update_one(  # take item from init owner
            {"discord_id": interaction.user.id},
            {"$inc": {f"inventory.{item}": -amount}},
        )

        await self.bot.db.economy.update_one(  # give item to target
            {"discord_id": user.id}, {"$inc": {f"inventory.{item}": amount}}
        )

        await interaction.response.send_message(
            f"You gave `{amount} {item}s` to {user.name}#{user.discriminator}"
        )

    @give.autocomplete("item")
    async def _give_items_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> List[app_commands.Choice[str]]:
        registration = await Registration(interaction.user.id).economy()

        item_list = registration["inventory"]

        return [
            app_commands.Choice(name=item, value=item)
            for item in item_list
            if item_list[item] > 0 and current.lower() in item.lower()
        ]

    exchange_commands = app_commands.Group(
        name="exchange", description="Commands for exchange"
    )

    @exchange_commands.command()
    @commands.guild_only()
    @app_commands.checks.cooldown(1, 10)
    async def templecoin(self, interaction: discord.Interaction, amount: int = None):
        """get templecoin with your copies & deletes"""

        await Registration(interaction.user.id).economy()

        user_data = await self.bot.db.economy.find_one(
            {"discord_id": interaction.user.id}
        )

        if user_data["reputation"] < 50:
            await interaction.response.send_message(
                "Your reputation is too low to exchange TempleCoin! Your reputation must be at least 50%",
                ephemeral=True,
            )

            return

        if amount is None or amount == 0:
            await interaction.response.send_message(
                f"You haven't specified how many TempleCoin you want to get\nCurrent exchange rates for TempleCoin:\n1 TempleCoin = `{exchange_values['TempleCoin']['copies']} copies` and `{exchange_values['TempleCoin']['deletes']} deletes`"
            )

            return

        if amount < 0:
            return

        copies_required = exchange_values["TempleCoin"]["copies"] * amount
        deletes_required = exchange_values["TempleCoin"]["deletes"] * amount

        if (
            user_data["copies"] < copies_required
            or user_data["deletes"] < deletes_required
        ):
            await interaction.response.send_message(
                "You have too little copies and/or deletes for this transaction!"
            )

            return

        await self.bot.db.economy.update_one(
            {"discord_id": interaction.user.id},
            {
                "$inc": {
                    "copies": -copies_required,
                    "deletes": -deletes_required,
                    "inventory.TempleCoin": amount,
                }
            },
        )

        await interaction.response.send_message(
            f"You've exchanged `{copies_required} copies` and `{deletes_required} deletes` for `{amount}` TempleCoin!"
        )

        await update_exchange_rates(self.bot)

    marketplace_commands = app_commands.Group(
        name="marketplace", description="Commands for interacting with the marketplace"
    )

    @marketplace_commands.command(
        name="view", description="View the available offerings on the marketplace"
    )
    @commands.guild_only()
    async def _marketplace_view(self, interaction: discord.Interaction):
        result = self.bot.db.economy_marketplace.find({}, {})
        _list = await result.to_list(10000)

        def sort_key(listing):
            if listing["listing_id"].startswith("LIMITED_"):
                return -10000000000000000

            return listing["price_per_item"]

        _list.sort(key=sort_key)

        embed = discord.Embed(
            title="Marketplace",
            description="Welcome to the marketplace!\nTo purchase an item, run `/marketplace buy <listing_id>`",
            colour=Enum.Embeds.Colors.Info,
        )

        for listing in _list:
            if not listing["stock"] > 0:
                continue

            embed.add_field(
                name=f"{listing['item']} | ID: {listing['listing_id']}",
                value=f"**Price**: `{listing['price_per_item']} TempleCoins / 1 item`\n**Stock**: `{listing['stock']}`",
                inline=False,
            )

        await interaction.response.send_message(embed=embed)

    @marketplace_commands.command(
        name="buy", description="Purchase something from the marketplace"
    )
    @commands.guild_only()
    async def _marketplace_buy(
        self, interaction: discord.Interaction, listing_id: str, amount: int = 1
    ):
        listing = await self.bot.db.economy_marketplace.find_one(
            {"listing_id": listing_id}
        )

        buyer_registration = await Registration(interaction.user.id).economy()

        buyer_balance = buyer_registration["inventory"].get("TempleCoin", 0)

        if amount < 1:
            return

        if listing is None:
            await interaction.response.send_message(
                "There is no listing with this listing id!", ephemeral=True
            )

            return

        item = listing["item"]
        stock = listing["stock"]
        price_per_item = listing["price_per_item"]

        if not item in ITEMS:
            await interaction.response.send_message("wtf how")

            return

        if amount > stock:
            await interaction.response.send_message(
                "You're trying to purchase more of the item than the listing has in stock!",
                ephemeral=True,
            )

            return

        if (
            (buyer_registration["inventory"].get(item, None) is not None)
            and listing_id.startswith("LIMITED_")
            or (amount > 1 and listing_id.startswith("LIMITED_"))
        ):
            await interaction.response.send_message(
                "This item is limited and therefore can't be purchased more than once!",
                ephemeral=True,
            )

            return

        if price_per_item * amount > buyer_balance:
            await interaction.response.send_message(
                "This purchase costs more TempleCoins than you have!", ephemeral=True
            )

            return

        if stock - amount == 0:
            await self.bot.db.economy_marketplace.delete_one(  # delete listing cuz stock = 0
                {"listing_id": listing_id}
            )

        else:
            await self.bot.db.economy_marketplace.update_one(  # remove items from stock
                {"listing_id": listing_id}, {"$inc": {"stock": -amount}}
            )

        await self.bot.db.economy.update_one(  # give owner templecoins after their item has been purchased
            {"discord_id": listing["owner"]["discord_id"]},
            {"$inc": {"inventory.TempleCoin": amount * price_per_item}},
        )

        await self.bot.db.economy.update_one(  # give buyer their item
            {"discord_id": interaction.user.id},
            {
                "$inc": {
                    "inventory.TempleCoin": -(amount * price_per_item),
                    f"inventory.{item}": amount,
                }
            },
        )

        await interaction.response.send_message(
            f"You successfully purchased `{amount}` `{item}s` for `{amount * price_per_item} TempleCoins`"
        )

    @marketplace_commands.command(
        name="sell", description="Sell something on the marketplace"
    )
    @commands.guild_only()
    async def _marketplace_sell(
        self,
        interaction: discord.Interaction,
        item: str,
        price_per_item: float,
        amount: int = 1,
    ):
        registration = await Registration(interaction.user.id).economy()

        if len(await get_marketplace_listings(interaction.user.id)) >= 3:
            await interaction.response.send_message(
                "You can't have more than 3 listings on the marketplace at once! Unsell one of them and try again",
                ephemeral=True,
            )

            return

        if item == "TempleCoin":
            await interaction.response.send_message(
                "This item can't be listed!", ephemeral=True
            )

            return

        if not item:
            await interaction.response.send_message(
                "You don't have this item!", ephemeral=True
            )

            return

        if registration["inventory"].get(item, 0) < amount:
            await interaction.response.send_message(
                "You don't have this much of the item to sell!", ephemeral=True
            )

            return

        if amount < 1 or price_per_item < 0:
            return

        await self.bot.db.economy.update_one(  # take item from owner's inventory
            {"discord_id": interaction.user.id},
            {"$inc": {f"inventory.{item}": -amount}},
        )

        listing_id = await Registration(  # create a new listing
            interaction.user.id
        ).economy_marketplace(item, amount, price_per_item)

        await interaction.response.send_message(
            f"You successfully listed `{amount}` `{item}s` on the marketplace for `{price_per_item} TempleCoins / 1 item`!\nListing ID: {listing_id}"
        )

    @_marketplace_sell.autocomplete("item")
    async def _sell_items_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> List[app_commands.Choice[str]]:
        registration = await Registration(interaction.user.id).economy()

        item_list = registration["inventory"]

        return [
            app_commands.Choice(name=item, value=item)
            for item in item_list
            if item_list[item] > 0
            and current.lower() in item.lower()
            and item != "TempleCoin"
        ]

    @marketplace_commands.command(
        name="unsell", description="Take your listing off the marketplace"
    )
    @commands.guild_only()
    async def _marketplace_unsell(
        self, interaction: discord.Interaction, listing_id: str
    ):
        listing_data = await self.bot.db.economy_marketplace.find_one(
            {"owner.discord_id": interaction.user.id, "listing_id": listing_id}
        )

        if not listing_data:
            await interaction.response.send_message(
                "This listing was not found, or it isn't yours!", ephemeral=True
            )

            return

        await self.bot.db.economy_marketplace.delete_one(
            {"owner.discord_id": interaction.user.id, "listing_id": listing_id}
        )

        await self.bot.db.economy.update_one(
            {"discord_id": interaction.user.id},
            {"$inc": {f'inventory.{listing_data["item"]}': listing_data["stock"]}},
        )

        await interaction.response.send_message(
            "Your listing was taken off the marketplace successfully!"
        )

    @_marketplace_unsell.autocomplete("listing_id")
    async def _unsell_items_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> List[app_commands.Choice[str]]:
        item_list = [
            listing["listing_id"]
            for listing in await get_marketplace_listings(interaction.user.id)
        ]

        return [
            app_commands.Choice(name=item, value=item)
            for item in item_list
            if current.lower() in item.lower()
        ]

    @marketplace_commands.command(
        name="get_listings",
        description="Get listing of a specific user (defaults to the user who ran the command)",
    )
    @commands.guild_only()
    async def _marketplace_get_listings(
        self, interaction: discord.Interaction, user: discord.User = None
    ):
        user = user or interaction.user

        listings = await get_marketplace_listings(user.id)

        if len(listings) == 0:
            await interaction.response.send_message(
                "This user has no listings!", ephemeral=True
            )

            return

        embed = discord.Embed(
            title=f"Listings of {user}", colour=Enum.Embeds.Colors.Info
        )

        for listing in listings:
            embed.add_field(
                name=f'{listing["item"]} | ID: {listing["listing_id"]}',
                value=f'**Price**: `{listing["price_per_item"]} / 1 item`\n**Stock**: `{listing["stock"]}`',
                inline=False,
            )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    """Setup Economy module

    Args:
        bot (discord.Bot): The bot class
    """
    await bot.add_cog(Economy(bot))
