"""
PersonalityUpdater — post-battle personality drift.

After each battle, each pet's personality weights are nudged
slightly toward reflecting what it actually did in combat.
Personality emerges from behavior, not from menus.
"""
from __future__ import annotations
from pet_battle.models import BattleResult, Pet, TurnRecord

# How much to shift a personality weight per battle.
# Small value = slow drift. Personality shouldn't flip after one fight.
_NUDGE = 0.05


def update(pet: Pet, result: BattleResult) -> None:
    """
    Nudge pet.personality based on how it fought this battle.
    Modifies the PersonalityProfile in-place.
    """
    log = result.battle_log

    # Early return: nothing to do if the log is empty.
    # An empty list is falsy in Python, so `if not log` is the idiomatic
    # way to check "is this list empty?".
    if not log:
        return

    # `result.winner is pet` uses identity comparison (`is`) to check
    # whether the winner object IS this specific pet object in memory.
    # This is correct here because we want to know "same object?",
    # not "same name?" — two pets could theoretically share a name.
    won = result.winner is pet

    # Figure out which column of the TurnRecord this pet occupies.
    is_pet_a = _is_pet_a(pet, result)

    # --- Tally what the pet actually played ---
    # `len(log)` is the number of turns.
    total = len(log)

    # `sum(1 for r in log if condition)` is a *generator expression*.
    # It's like a list comprehension but doesn't build the list — it just
    # counts. For each TurnRecord r in the log, if the condition is true,
    # it contributes 1 to the sum. Equivalent to:
    #   count = 0
    #   for r in log:
    #       if _card_type(r, is_pet_a) == "aggressive":
    #           count += 1
    aggressive = sum(1 for r in log if _card_type(r, is_pet_a) == "aggressive")
    defensive  = sum(1 for r in log if _card_type(r, is_pet_a) == "defensive")
    tricky     = sum(1 for r in log if _card_type(r, is_pet_a) == "tricky")
    swaps      = sum(1 for r in log if _swapped(r, is_pet_a))

    # `log[-1]` accesses the LAST element of the list.
    # Negative indices count from the end: -1 = last, -2 = second to last.
    last_card  = log[-1].pet_a_card if is_pet_a else log[-1].pet_b_card

    # Another local alias to keep lines short.
    p = pet.personality

    # Nudge weights based on what the pet actually did this battle.
    # `aggressive / total` is a ratio between 0.0 and 1.0.
    # If the pet played aggressive cards more than half the time, the
    # aggression weight goes up; otherwise it drifts slightly down.
    p.aggression = _nudge_toward(p.aggression, aggressive / total)
    p.caution    = _nudge_toward(p.caution,    defensive  / total)
    p.cunning    = _nudge_toward(p.cunning,    tricky     / total)

    # Extra boldness if they won on a slow, high-commitment card.
    if won and last_card.speed_tier == 3:
        # `min(1.0, x + _NUDGE)` clamps the result so it never exceeds 1.0.
        p.bold = min(1.0, p.bold + _NUDGE)

    # Cunning boost if intuition swaps contributed to a win.
    if swaps > 0 and won:
        p.cunning = min(1.0, p.cunning + _NUDGE)

    p.experience += 1  # shorthand for p.experience = p.experience + 1

    # --- Trait accumulation ---
    # `not in` checks membership: is this string NOT in the list?
    # We check before appending so we don't get duplicates.
    if p.aggression > 0.7 and "scrappy" not in p.traits:
        p.traits.append("scrappy")
    if p.caution > 0.7 and "calculated" not in p.traits:
        p.traits.append("calculated")
    if p.cunning > 0.7 and "trickster" not in p.traits:
        p.traits.append("trickster")
    if swaps >= 3 and "perceptive" not in p.traits:
        p.traits.append("perceptive")


# ---------------------------------------------------------------------------
# Helpers (private by convention — underscore prefix)
# ---------------------------------------------------------------------------

def _nudge_toward(current: float, ratio: float) -> float:
    """Move current slightly toward ratio, clamped to [0, 1]."""
    # `ratio > 0.5` means the pet played this type of card more than half
    # the time, so we nudge the weight up. Otherwise nudge it down,
    # but slower (0.5 multiplier) — it's easier to gain a trait than lose it.
    if ratio > 0.5:
        return min(1.0, current + _NUDGE)
    else:
        return max(0.0, current - _NUDGE * 0.5)


def _is_pet_a(pet: Pet, result: BattleResult) -> bool:
    """Determine if pet is the 'a' slot using the refs stored in BattleResult."""
    # `result.pet_a is pet` — identity check (same object in memory, not just equal).
    # BattleEngine stores the original pet objects in BattleResult specifically
    # so we can do this check here without passing extra arguments around.
    return result.pet_a is pet


def _card_type(record: TurnRecord, is_pet_a: bool) -> str:
    # A *conditional expression* (also called a ternary expression):
    #   value_if_true if condition else value_if_false
    # Equivalent to an if/else block but fits on one line when simple.
    return record.pet_a_card_type if is_pet_a else record.pet_b_card_type


def _swapped(record: TurnRecord, is_pet_a: bool) -> bool:
    return record.swapped_a if is_pet_a else record.swapped_b
