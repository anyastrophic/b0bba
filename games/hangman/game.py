import random
from modules.placeholders import Placeholder

words = []
with open("./games/words.txt", "r", encoding="utf-8") as f:
    words = f.read().splitlines()

    f.close()


class HangmanLetter:
    def __init__(self, letter) -> None:
        self.letter = letter
        self.uncovered = False


class HangmanGame:
    def __init__(self, owner: str) -> None:
        self.owner = owner
        self.tries = 5
        self.word = random.choice(words)
        self.word_sequence = []

        for letter in self.word:
            self.word_sequence.append(HangmanLetter(letter))

        random_letter = random.choice(self.word)

        for letter_obj in self.word_sequence:
            if letter_obj.letter == random_letter:
                letter_obj.uncovered = True

    async def get_output_word(self) -> str:
        word = ""

        for letter_obj in self.word_sequence:
            if letter_obj.uncovered is True:
                word = word + letter_obj.letter
            else:
                word = word + "_"

        return word

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

    async def guess(self, guess) -> str:
        if guess.lower() == self.word:
            return "win"

        result = False

        for letter_obj in self.word_sequence:
            if letter_obj.letter == guess.lower() and letter_obj.uncovered is False:
                letter_obj.uncovered = True
                result = True

        if result is False:
            self.tries -= 1

        if self.tries == 0:
            return "lose"

        if await self.get_output_word() == self.word:
            return "win"

        # nothing returned, so return mid-game

        return "mid-game"
