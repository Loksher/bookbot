"""
Hard-coded starter ability cards and demo pets.

catalog.py is the only file that should contain raw stat numbers.
Everything else works with Pet/AbilityCard instances.
"""
from __future__ import annotations
from pet_battle.models import AbilityCard, PersonalityProfile, Pet

# ---------------------------------------------------------------------------
# Starter ability cards
# ---------------------------------------------------------------------------
# These are module-level constants (ALL_CAPS convention).
# Each one is an AbilityCard *instance* created by calling the dataclass
# like a function. The dataclass __init__ handles all the wiring.
#
# Notice we use keyword arguments (name=, damage=, ...) instead of
# positional ones. With many arguments this makes the code far more readable
# and means the order doesn't matter.

IRON_FANG = AbilityCard(
    name="Iron Fang", damage=18, speed_tier=1, card_type="aggressive", cooldown=0
)
QUICKSTRIKE = AbilityCard(
    name="Quickstrike", damage=12, speed_tier=1, card_type="aggressive", cooldown=0
)
ROCKSLIDE = AbilityCard(
    name="Rockslide", damage=25, speed_tier=3, card_type="aggressive", cooldown=1
)
STONE_WALL = AbilityCard(
    name="Stone Wall", damage=0, speed_tier=2, card_type="defensive",
    effect="shield", cooldown=1
)
STATIC_VEIL = AbilityCard(
    name="Static Veil", damage=0, speed_tier=1, card_type="defensive",
    effect="shield", cooldown=2
)
DRAIN_BITE = AbilityCard(
    name="Drain Bite", damage=14, speed_tier=2, card_type="tricky",
    effect="drain", cooldown=1
)
SMOKESCREEN = AbilityCard(
    name="Smokescreen", damage=0, speed_tier=1, card_type="tricky",
    effect="stun", cooldown=3
)
MIRROR_STANCE = AbilityCard(
    name="Mirror Stance", damage=8, speed_tier=2, card_type="tricky", cooldown=0
)

# A plain list of all cards — useful later for a card picker or shop feature.
ALL_CARDS = [
    IRON_FANG, QUICKSTRIKE, ROCKSLIDE, STONE_WALL,
    STATIC_VEIL, DRAIN_BITE, SMOKESCREEN, MIRROR_STANCE,
]


# ---------------------------------------------------------------------------
# Demo pets
# ---------------------------------------------------------------------------
# WHY functions instead of constants like EMBER = Pet(...)?
#
# Because Pet is a *mutable* object — its hp, cooldowns, and stunned flag
# all change during a battle. If we stored it as a module-level constant,
# the second battle would start with whatever hp Ember had at the end of the
# first one. Functions give us a fresh instance every time we call them.

def make_ember() -> Pet:
    """Ember — fast, aggressive starter. High intuition."""
    return Pet(
        name="Ember",
        hp=80,
        max_hp=80,
        attack=12,
        defense=4,
        speed=8,
        intuition=7,
        # A list literal passed directly as an argument.
        # These are the SAME card objects as the constants above —
        # Ember shares a reference to IRON_FANG, she doesn't get her own copy.
        # That's fine because AbilityCard is never mutated during battle.
        ability_cards=[IRON_FANG, QUICKSTRIKE, ROCKSLIDE, SMOKESCREEN],
        personality=PersonalityProfile(
            aggression=0.7, caution=0.2, cunning=0.3, bold=0.4
        ),
    )


def make_glacius() -> Pet:
    """Glacius — tanky, defensive starter. Low intuition."""
    return Pet(
        name="Glacius",
        hp=90,
        max_hp=90,
        attack=9,
        defense=7,
        speed=5,
        intuition=3,
        ability_cards=[STONE_WALL, STATIC_VEIL, DRAIN_BITE, ROCKSLIDE],
        personality=PersonalityProfile(
            aggression=0.2, caution=0.7, cunning=0.4, bold=0.3
        ),
    )


# ---------------------------------------------------------------------------
# Custom pet factory for the web server / multiplayer mode
# ---------------------------------------------------------------------------

#: Maps archetype name to (hp, attack, defense, speed, intuition, cards).
_ARCHETYPES: dict[str, tuple[int, int, int, int, int, list[AbilityCard]]] = {
    "striker": (75, 13, 3, 9, 7, [IRON_FANG, QUICKSTRIKE, ROCKSLIDE, SMOKESCREEN]),
    "drifter": (85, 10, 5, 6, 6, [QUICKSTRIKE, DRAIN_BITE, MIRROR_STANCE, ROCKSLIDE]),
    "guardian": (100, 8, 8, 4, 3, [STONE_WALL, STATIC_VEIL, DRAIN_BITE, ROCKSLIDE]),
}


def make_custom_pet(
    name: str,
    archetype: str,
    aggression: float,
    caution: float,
    cunning: float,
    bold: float,
) -> Pet:
    """Create a player-defined pet from an archetype + personality weights.

    archetype must be one of: "striker", "drifter", "guardian".
    Personality weights should be floats in [0.0, 1.0].
    """
    archetype = archetype if archetype in _ARCHETYPES else "drifter"
    hp, attack, defense, speed, intuition, cards = _ARCHETYPES[archetype]
    return Pet(
        name=name,
        hp=hp,
        max_hp=hp,
        attack=attack,
        defense=defense,
        speed=speed,
        intuition=intuition,
        ability_cards=cards,
        personality=PersonalityProfile(
            aggression=max(0.0, min(1.0, aggression)),
            caution=max(0.0, min(1.0, caution)),
            cunning=max(0.0, min(1.0, cunning)),
            bold=max(0.0, min(1.0, bold)),
        ),
    )
