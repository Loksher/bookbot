from __future__ import annotations
import random
from pet_battle.llm_interface import LLMBackend
from pet_battle.models import AbilityCard, Pet

# Flavor text templates keyed by (card_type, speed_tier).
# {pet} is replaced with the pet's name.
_FLAVOR: dict[tuple[str, int], list[str]] = {
    ("aggressive", 1): [
        "{pet} lunges without hesitation.",
        "{pet} sees an opening and strikes.",
        "{pet} launches a ferocious quick attack.",
    ],
    ("aggressive", 2): [
        "{pet} winds up and swings hard.",
        "{pet} charges forward with conviction.",
        "{pet} presses the attack.",
    ],
    ("aggressive", 3): [
        "{pet} takes a moment, then unleashes a devastating blow.",
        "{pet} commits fully to the heavy strike.",
        "{pet} draws back and releases everything.",
    ],
    ("defensive", 1): [
        "{pet} snaps into a guard stance instantly.",
        "{pet} raises a quick barrier.",
        "{pet} reacts fast, shielding against the incoming hit.",
    ],
    ("defensive", 2): [
        "{pet} holds its ground warily.",
        "{pet} braces for impact.",
        "{pet} adopts a steady defensive posture.",
    ],
    ("defensive", 3): [
        "{pet} settles in, fortifying its position slowly.",
        "{pet} takes a breath and builds a solid wall.",
        "{pet} commits to the long-form defense.",
    ],
    ("tricky", 1): [
        "{pet} moves fast before the opponent can read the intention.",
        "{pet} acts quickly, keeping the enemy guessing.",
        "{pet} darts in with a slippery feint.",
    ],
    ("tricky", 2): [
        "{pet} sets up something subtle.",
        "{pet} keeps its options open with a crafty move.",
        "{pet} plays it clever.",
    ],
    ("tricky", 3): [
        "{pet} takes its time, setting the trap.",
        "{pet} waits... patiently.",
        "{pet} lets the opponent commit first, then counters.",
    ],
}

_FALLBACK = "{pet} acts."


class MockLLM(LLMBackend):
    """
    Personality-weighted random card picker.

    Scores each available card using the pet's personality weights,
    then does a weighted random selection. Returns a pre-written
    flavor line. No network calls — this is also the game's designed
    fallback when inference is unavailable.
    """

    def choose_card(
        self,
        pet: Pet,
        available_cards: list[AbilityCard],
        enemy_snapshot: dict,
    ) -> tuple[AbilityCard, str]:
        p = pet.personality
        scores = []
        for card in available_cards:
            score = 1.0
            if card.card_type == "aggressive":
                score += p.aggression * 3.0
            elif card.card_type == "defensive":
                score += p.caution * 3.0
            elif card.card_type == "tricky":
                score += p.cunning * 3.0

            # Bold pets lean into slow high-damage swings
            if card.speed_tier == 3:
                score += p.bold * 2.0
            elif card.speed_tier == 1:
                score += (1.0 - p.bold) * 1.5

            # Slight tiebreaker toward higher damage
            score += card.damage * 0.1
            scores.append(score)

        (choice,) = random.choices(available_cards, weights=scores, k=1)
        flavor = self._flavor(pet.name, choice)
        return choice, flavor

    @staticmethod
    def _flavor(pet_name: str, card: AbilityCard) -> str:
        key = (card.card_type, card.speed_tier)
        templates = _FLAVOR.get(key, [_FALLBACK])
        return random.choice(templates).replace("{pet}", pet_name)
