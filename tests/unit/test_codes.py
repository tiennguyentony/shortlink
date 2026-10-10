import random

import pytest

from shortlink.codes import FixedCodes, RandomCodes
from shortlink.config import Settings


def test_random_codes_use_configured_length_and_alphabet():
    settings = Settings()
    codes = RandomCodes(settings.code_length, settings.code_alphabet, random.Random(42))
    for _ in range(200):
        code = codes.new_code()
        assert len(code) == 6
        assert set(code) <= set(settings.code_alphabet)


def test_alphabet_has_no_lookalike_characters():
    assert not set("01ilo") & set(Settings().code_alphabet)


def test_random_codes_are_reproducible_with_a_seeded_rng():
    a = RandomCodes(6, "abc123", random.Random(7))
    b = RandomCodes(6, "abc123", random.Random(7))
    assert [a.new_code() for _ in range(5)] == [b.new_code() for _ in range(5)]


def test_fixed_codes_hand_out_codes_in_order():
    codes = FixedCodes(["aaaaaa", "bbbbbb"])
    assert codes.new_code() == "aaaaaa"
    assert codes.new_code() == "bbbbbb"
    with pytest.raises(RuntimeError):
        codes.new_code()
