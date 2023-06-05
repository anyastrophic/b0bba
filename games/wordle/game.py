import random

valid_words = []
with open("./games/wordle/valid_words.txt", "r", encoding="utf-8") as f:
    valid_words = f.read().splitlines()

    f.close()

words = []
with open("./games/wordle/words.txt", "r", encoding="utf-8") as f:
    words = f.read().splitlines()

    f.close()


class WordleGame:
    def __init__(self, owner: str) -> None:
        self.owner = owner
        self.word = random.choice(words)
        self.guesses = []

    async def generate_emoji_word(self, guess: str):
        yellow = "🟨"
        green = "🟩"
        grey = "⬜"

        letters = {}

        for letter in self.word:
            if not letter in letters:
                letters[letter] = 0
            letters[letter] = letters[letter] + 1

        string = ""

        for i, letter in enumerate(guess):
            if letter in self.word and letter == self.word[i]:
                string = string + green
                letters[letter] = letters[letter] - 1
            elif letter in self.word and letters[letter] > 0:
                letters[letter] = letters[letter] - 1
                string = string + yellow
            else:
                string = string + grey

        return string + " " + " ".join(guess)

    async def get_output(self, _type="mid-game") -> str:
        string = ""

        black = "⬛"

        for i in self.guesses:
            string += f"\n{await self.generate_emoji_word(i)}"

        for i in range(6 - len(self.guesses)):
            string += f"\n{black}{black}{black}{black}{black}"

        if _type == "mid-game":
            return f"{self.owner}'s wordle!\nGuess the word:{string}"
        elif _type == "lose":
            return f"{self.owner}'s wordle!\nYou lost!\nThe wordle:{string}\nThe word was: {self.word}"
        elif _type == "win":
            return f"{self.owner}'s wordle!\nYou won!\nThe wordle:{string}\nThe word was: {self.word}"

    async def guess(self, guess: str):
        if not guess in valid_words:
            return "mid-game"

        self.guesses = self.guesses + [guess]

        if guess == self.word:
            return "win"

        if len(self.guesses) == 6:
            return "lose"

        return "mid-game"
