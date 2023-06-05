import random
from modules.placeholders import Placeholder

words = []
with open("./games/words.txt", "r", encoding="utf-8") as f:
    words = f.read().splitlines()

    f.close()


class UnscrambleGame:
    def __init__(self, owner: str) -> None:
        self.tries = 2
        self.owner = owner
        self.word = random.choice(words)
        self.scrambled_word = list(self.word)
        random.shuffle(self.scrambled_word)
        self.scrambled_word = "".join(self.scrambled_word)

    async def get_output_word(self) -> str:
        return self.scrambled_word

    async def get_output(self, _type="mid-game") -> str:
        match _type:
            case "mid-game":
                return Placeholder.Games.Hangman.GameResponses.MidGame.format(
                    self.owner, await self.get_output_word(), self.tries
                )
            case "lose":
                return Placeholder.Games.Hangman.GameResponses.Lose.format(
                    self.owner, self.word
                )
            case "win":
                return Placeholder.Games.Hangman.GameResponses.Win.format(
                    self.owner, self.word
                )

    async def scramble_word(self) -> None:
        self.scrambled_word = list(self.word)
        random.shuffle(self.scrambled_word)
        self.scrambled_word = "".join(self.scrambled_word)

        if self.scrambled_word == self.word:
            await self.scramble_word()

    async def guess(self, guess) -> str:
        if guess.lower() == self.word:
            return "win"

        self.tries -= 1
        await self.scramble_word()

        if self.tries == 0:
            return "lose"

        return "mid-game"
