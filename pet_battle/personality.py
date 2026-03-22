"""
PersonalityUpdater — post-battle personality drift.

After each battle, each pet's personality weights are nudged
slightly toward reflecting what it actually did in combat.
Personality emerges from behavior, not from menus.
"""
from __future__ import annotations
from pet_battle.models import BattleResult, Pet, TurnRecord

_NUDGE = 0.05  # all changes are small; personality drifts slowly


def update(pet: Pet, result: BattleResult) -> None:
    """
    Nudge pet.personality based on how it fought this battle.
    Modifies the PersonalityProfile in-place.
    """
    log = result.battle_log
    if not log:
        return

    won = result.winner is pet
    is_pet_a = _is_pet_a(pet, result)

    # Tally what the pet actually played
    total = len(log)
    aggressive = sum(1 for r in log if _card_type(r, is_pet_a) == "aggressive")
    defensive  = sum(1 for r in log if _card_type(r, is_pet_a) == "defensive")
    tricky     = sum(1 for r in log if _card_type(r, is_pet_a) == "tricky")
    swaps      = sum(1 for r in log if _swapped(r, is_pet_a))
    last_card  = log[-1].pet_a_card if is_pet_a else log[-1].pet_b_card

    p = pet.personality

    # Nudge each weight toward the ratio actually played
    p.aggression = _nudge_toward(p.aggression, aggressive / total)
    p.caution    = _nudge_toward(p.caution,    defensive  / total)
    p.cunning    = _nudge_toward(p.cunning,    tricky     / total)

    # Bold: if the pet won on a slow heavy card, grow bolder
    if won and last_card.speed_tier == 3:
        p.bold = min(1.0, p.bold + _NUDGE)

    # Cunning boost: intuition swaps that led to a win
    if swaps > 0 and won:
        p.cunning = min(1.0, p.cunning + _NUDGE)

    p.experience += 1

    # Trait accumulation — append-only, deduplicated
    if p.aggression > 0.7 and "scrappy" not in p.traits:
        p.traits.append("scrappy")
    if p.caution > 0.7 and "calculated" not in p.traits:
        p.traits.append("calculated")
    if p.cunning > 0.7 and "trickster" not in p.traits:
        p.traits.append("trickster")
    if swaps >= 3 and "perceptive" not in p.traits:
        p.traits.append("perceptive")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _nudge_toward(current: float, ratio: float) -> float:
    """Move current slightly toward ratio, clamped to [0, 1]."""
    if ratio > 0.5:
        return min(1.0, current + _NUDGE)
    else:
        return max(0.0, current - _NUDGE * 0.5)


def _is_pet_a(pet: Pet, result: BattleResult) -> bool:
    """Determine if pet is the 'a' slot using the refs stored in BattleResult."""
    return result.pet_a is pet


def _card_type(record: TurnRecord, is_pet_a: bool) -> str:
    return record.pet_a_card_type if is_pet_a else record.pet_b_card_type


def _swapped(record: TurnRecord, is_pet_a: bool) -> bool:
    return record.swapped_a if is_pet_a else record.swapped_b
