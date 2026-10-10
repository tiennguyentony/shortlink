"""Short code generation.

Codes are 8 characters drawn from the full base62 alphabet (a-z, A-Z, 0-9),
which gives 62**8, about 218 trillion, possible codes. At our volume a
collision is practically impossible, so callers don't need to retry.
"""

import random
from typing import Protocol


class CodeGenerator(Protocol):
    def new_code(self) -> str: ...


class RandomCodes:
    def __init__(self, length: int, alphabet: str, rng: random.Random | None = None):
        self.length = length
        self.alphabet = alphabet
        self._rng = rng or random.SystemRandom()

    def new_code(self) -> str:
        return "".join(self._rng.choice(self.alphabet) for _ in range(self.length))


class FixedCodes:
    """Hands out a predefined list of codes. For tests."""

    def __init__(self, codes: list[str]):
        self._codes = list(codes)

    def new_code(self) -> str:
        if not self._codes:
            raise RuntimeError("FixedCodes ran out of codes")
        return self._codes.pop(0)
