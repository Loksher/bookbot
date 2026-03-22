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

ALL_CARDS = [
    IRON_FANG, QUICKSTRIKE, ROCKSLIDE, STONE_WALL,
    STATIC_VEIL, DRAIN_BITE, SMOKESCREEN, MIRROR_STANCE,
]


# ---------------------------------------------------------------------------
# Demo pets
# ---------------------------------------------------------------------------

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
