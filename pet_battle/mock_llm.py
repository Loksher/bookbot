from __future__ import annotations
import random
from pet_battle.llm_interface import LLMBackend
from pet_battle.models import AbilityCard, Pet

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------
# Names in ALL_CAPS are a Python convention for module-level constants —
# values that are set once and never changed. Python doesn't enforce this,
# it's just a signal to other programmers (and your future self).
#
# This dictionary maps a (card_type, speed_tier) pair to a list of strings.
# The key is a *tuple* — an immutable, ordered pair used here because
# dictionary keys must be hashable (unchangeable), and lists aren't.
#
# The type hint `dict[tuple[str, int], list[str]]` reads as:
#   "a dict whose keys are (str, int) tuples and values are lists of strings"
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

# A fallback string used when no matching template exists.
_FALLBACK = "{pet} acts."


# `MockLLM(LLMBackend)` means MockLLM *inherits* from LLMBackend.
# Inheritance means: "this class is a more specific version of LLMBackend."
# Because LLMBackend is abstract and requires `choose_card`, Python will
# raise an error if we forget to implement it here.
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
        # `p` is a shorthand alias so we don't have to write `pet.personality`
        # on every line. Python assigns by reference, so p IS pet.personality —
        # the same object, just a shorter name.
        p = pet.personality

        # Build a parallel list of scores — one float per card.
        # `scores[i]` will correspond to `available_cards[i]`.
        scores = []
        for card in available_cards:
            # Start every card with a base score of 1.0 so no card has zero
            # probability, even if the personality doesn't favour it at all.
            score = 1.0

            # Add a bonus based on whether this card's type matches the
            # pet's personality. A very aggressive pet (p.aggression = 0.9)
            # gets +2.7 on aggressive cards; a timid pet (p.aggression = 0.1)
            # only gets +0.3.
            if card.card_type == "aggressive":
                score += p.aggression * 3.0
            elif card.card_type == "defensive":
                score += p.caution * 3.0
            elif card.card_type == "tricky":
                score += p.cunning * 3.0

            # Bold pets lean into slow high-damage swings;
            # cautious pets prefer fast, safer cards.
            if card.speed_tier == 3:
                score += p.bold * 2.0
            elif card.speed_tier == 1:
                # `1.0 - p.bold` inverts the weight: low bold → high bonus for fast cards
                score += (1.0 - p.bold) * 1.5

            # Slight tiebreaker toward higher damage cards.
            # * 0.1 keeps this from overwhelming the personality weights above.
            score += card.damage * 0.1
            scores.append(score)

        # `random.choices` picks k items from the population, using weights
        # to make higher-scored items more likely. It always returns a list,
        # even when k=1 — that's why we unpack it with `(choice,) =`.
        #
        # The comma in `(choice,)` is what makes it a tuple unpack, not
        # just parentheses. It tells Python: "there's exactly one item; put
        # it in `choice`." Without the comma it would just be `choice = [card]`.
        (choice,) = random.choices(available_cards, weights=scores, k=1)

        flavor = self._flavor(pet.name, choice)
        return choice, flavor  # returning a tuple — parentheses are optional

    # @staticmethod marks a method that doesn't need `self` — it doesn't
    # access any instance data. We could make it a plain module-level
    # function, but putting it here groups it logically with the class.
    @staticmethod
    def _flavor(pet_name: str, card: AbilityCard) -> str:
        # Build the lookup key as a tuple from the card's properties.
        key = (card.card_type, card.speed_tier)

        # dict.get(key, default) returns the value if the key exists,
        # or default if it doesn't — avoids a KeyError for unknown combos.
        templates = _FLAVOR.get(key, [_FALLBACK])

        # `random.choice` picks one item uniformly at random from a list.
        # `.replace("{pet}", pet_name)` substitutes the placeholder with
        # the actual pet's name — a simple manual template system.
        return random.choice(templates).replace("{pet}", pet_name)
