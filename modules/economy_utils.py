import random
from yahoo_finance_async import OHLC


async def get_stock_info(name: str):
    result = await OHLC.fetch(symbol=name)
    return result


def clamp(value, _max, _min):
    return max(min(value, _max), _min)


def probably(chance):
    chance = (clamp(chance, 1, 0)) * 100
    return random.randint(0, 100) < chance


async def get_rarity(luck_addend: float):
    rarity = None
    luck_addend = luck_addend / 10

    if probably((60 + luck_addend) / 100):
        rarity = "common"

        if probably((60 + luck_addend) / 100):
            rarity = "uncommon"

            if probably((60 + luck_addend) / 100):
                rarity = "rare"

                if probably((60 + luck_addend) / 100):
                    rarity = "very rare"

                    if probably((60 + luck_addend) / 100):
                        rarity = "epic"

                        if probably((60 + luck_addend) / 100):
                            rarity = "legendary"

                            if probably((60 + luck_addend) / 100):
                                rarity = "mythic"

    return rarity
