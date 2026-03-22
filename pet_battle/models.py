# `from __future__ import annotations` makes ALL type hints in this file
# behave as strings at runtime. Without it, writing `list[AbilityCard]` as
# a type hint would crash on Python < 3.10 because the class might not exist
# yet when the line is parsed. This one import future-proofs all your hints.
from __future__ import annotations

# `dataclass` and `field` come from the standard library module `dataclasses`.
# They let you define simple data-holding classes without writing boilerplate
# like __init__, __repr__, and __eq__ by hand.
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# @dataclass
# ---------------------------------------------------------------------------
# Decorators are functions that wrap another function or class to add
# behaviour. The `@` syntax means "call dataclass() on the class below and
# replace it with the result."
#
# @dataclass reads the class body and automatically generates:
#   __init__   — so you can write AbilityCard(name="Iron Fang", damage=18, ...)
#   __repr__   — nice string representation for debugging (try print(card))
#   __eq__     — two instances are equal when all their fields are equal
# ---------------------------------------------------------------------------

@dataclass
class AbilityCard:
    # Each line below is a *field*. The syntax is:  name: type = default
    # Fields WITHOUT a default are required arguments in __init__.
    # Fields WITH a default (like cooldown=0) are optional — they must come
    # after all required fields, same rule as regular function parameters.
    name: str
    damage: int
    speed_tier: int          # 1=fast, 2=normal, 3=slow (lower resolves first)
    card_type: str           # "aggressive" | "defensive" | "tricky"
    cooldown: int = 0        # turns locked after use (0 = always available)

    # `str | None` is a *union type* — the value can be a string OR None.
    # None is Python's way of saying "no value". It's not the same as 0 or "".
    effect: str | None = None  # "shield" | "drain" | "stun" | None


@dataclass
class PersonalityProfile:
    # `float` is a decimal number (0.5, 0.73, etc.).
    # These weights are independent — they don't need to add up to 1.0.
    aggression: float = 0.5    # weight toward aggressive cards
    caution: float = 0.5       # weight toward defensive cards
    cunning: float = 0.5       # weight toward tricky cards
    bold: float = 0.5          # willingness to use slow/high-damage cards
    experience: int = 0        # battle count

    # WHY field(default_factory=list) instead of traits: list = []?
    #
    # This is one of the most common Python gotchas. If you write:
    #   traits: list = []
    # then ALL instances of PersonalityProfile share the SAME list object.
    # Appending to one pet's traits would affect every pet!
    #
    # `default_factory=list` tells the dataclass: "call list() freshly for
    # each new instance", so every pet gets its own separate list.
    traits: list[str] = field(default_factory=list)

    # A *method* is a function that belongs to a class. It always receives
    # the instance as its first argument, conventionally named `self`.
    # `self` is how you access the instance's own data inside the method.
    def to_dict(self) -> dict:
        # `round(value, 3)` limits floats to 3 decimal places so the output
        # looks clean. Floats have tiny rounding errors under the hood
        # (try 0.1 + 0.2 in the Python REPL to see what we mean).
        return {
            "aggression": round(self.aggression, 3),
            "caution": round(self.caution, 3),
            "cunning": round(self.cunning, 3),
            "bold": round(self.bold, 3),
            "experience": self.experience,
            "traits": self.traits,
        }


@dataclass
class Pet:
    name: str
    hp: int
    max_hp: int
    attack: int
    defense: int
    speed: int
    intuition: int              # 1–10 scale
    ability_cards: list[AbilityCard]
    personality: PersonalityProfile

    # dict[str, int] means: a dictionary whose keys are strings and values
    # are integers. Here it maps a card name → how many turns it's locked.
    # Same default_factory trick as traits above — each pet needs its own dict.
    cooldowns: dict[str, int] = field(default_factory=dict)
    stunned: bool = False

    # __post_init__ is a special method the dataclass calls automatically
    # AFTER __init__ finishes. Use it for setup that depends on other fields
    # already being set. Here we make sure every card has an entry in
    # cooldowns, defaulting to 0 (ready to use).
    def __post_init__(self):
        for card in self.ability_cards:
            # dict.setdefault(key, default) adds the key with the default
            # value ONLY if the key isn't already there. It's a safe way to
            # initialise without overwriting existing data.
            self.cooldowns.setdefault(card.name, 0)

    def available_cards(self) -> list[AbilityCard]:
        # This is a *list comprehension* — a compact way to build a list.
        # It reads: "give me every card c, for each c in self.ability_cards,
        # but only if its cooldown is currently 0."
        #
        # dict.get(key, default) returns the value for key, or default if
        # the key doesn't exist — safer than cooldowns[c.name] which would
        # raise a KeyError if somehow the key was missing.
        return [c for c in self.ability_cards if self.cooldowns.get(c.name, 0) == 0]


@dataclass
class TurnRecord:
    # This class is a snapshot of one turn. It's used by personality.py after
    # the battle to figure out how each pet fought.
    turn_number: int
    pet_a_card: AbilityCard
    pet_b_card: AbilityCard
    pet_a_flavor: str
    pet_b_flavor: str
    pet_a_hp_after: int
    pet_b_hp_after: int
    swapped_a: bool
    swapped_b: bool
    # Fields with defaults come last (Python enforces this in dataclasses too)
    pet_a_card_type: str = ""   # card_type of the card pet_a actually played
    pet_b_card_type: str = ""


@dataclass
class BattleResult:
    # `Pet | None` means the winner could be a Pet, or None (in a draw).
    winner: Pet | None
    loser: Pet | None
    turns: int
    battle_log: list[TurnRecord]
    # These store references to the original pet objects so personality.py
    # can identify which slot (a or b) a given pet occupied.
    # The `is` operator checks object *identity* — whether two names point
    # to the exact same object in memory, not just equal values.
    pet_a: Pet | None = None
    pet_b: Pet | None = None
