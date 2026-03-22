from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class AbilityCard:
    name: str
    damage: int
    speed_tier: int          # 1=fast, 2=normal, 3=slow (lower resolves first)
    card_type: str           # "aggressive" | "defensive" | "tricky"
    cooldown: int = 0        # turns locked after use (0 = always available)
    effect: str | None = None  # "shield" | "drain" | "stun" | None


@dataclass
class PersonalityProfile:
    aggression: float = 0.5    # weight toward aggressive cards
    caution: float = 0.5       # weight toward defensive cards
    cunning: float = 0.5       # weight toward tricky cards
    bold: float = 0.5          # willingness to use slow/high-damage cards
    experience: int = 0        # battle count
    traits: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
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
    cooldowns: dict[str, int] = field(default_factory=dict)
    stunned: bool = False

    def __post_init__(self):
        for card in self.ability_cards:
            self.cooldowns.setdefault(card.name, 0)

    def available_cards(self) -> list[AbilityCard]:
        return [c for c in self.ability_cards if self.cooldowns.get(c.name, 0) == 0]


@dataclass
class TurnRecord:
    turn_number: int
    pet_a_card: AbilityCard
    pet_b_card: AbilityCard
    pet_a_flavor: str
    pet_b_flavor: str
    pet_a_hp_after: int
    pet_b_hp_after: int
    swapped_a: bool
    swapped_b: bool
    pet_a_card_type: str = ""   # card_type of the card pet_a actually played
    pet_b_card_type: str = ""


@dataclass
class BattleResult:
    winner: Pet | None
    loser: Pet | None
    turns: int
    battle_log: list[TurnRecord]
    pet_a: Pet | None = None   # populated by BattleEngine so personality.py can identify slots
    pet_b: Pet | None = None
