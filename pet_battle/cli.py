"""
Pretty-print helpers for turn-by-turn battle output.
All formatting lives here; battle_engine.py just calls these functions.
"""
from __future__ import annotations
from pet_battle.models import AbilityCard, Pet

# Module-level constants used by multiple functions below.
# Defining them once here means changing the separator width is one edit.
_SEP = "=" * 60        # "=" * 60 repeats the string 60 times
_CARD_NAME_WIDTH = 16  # how many characters to reserve for a card name


def print_battle_header(pet_a: Pet, pet_b: Pet) -> None:
    print(_SEP)
    # f-strings (formatted string literals): the f prefix means Python will
    # evaluate any expression inside {} and insert the result.
    # f"BATTLE: {pet_a.name}" → "BATTLE: Ember"
    print(f"  BATTLE: {pet_a.name} vs. {pet_b.name}")
    print(_SEP)
    _print_pet_stats(pet_a)
    _print_pet_stats(pet_b)
    print(_SEP)
    print()  # print() with no arguments prints a blank line


def print_turn_header(turn: int) -> None:
    print(f"--- Turn {turn} ---")


def print_card_selection(pet: Pet, card: AbilityCard, flavor: str, swapped: bool) -> None:
    # String slicing: `card.card_type[:3]` takes the first 3 characters.
    # [:3] means "from the start up to (but not including) index 3".
    # .upper() converts to uppercase. "aggressive"[:3].upper() → "AGG"
    card_type_tag = card.card_type[:3].upper()

    # str.ljust(width) pads the string with spaces on the RIGHT to reach
    # `width` total characters. This aligns all card names in a column.
    # "Iron Fang".ljust(16) → "Iron Fang       "
    name_col = card.name.ljust(_CARD_NAME_WIDTH)

    # A conditional expression: if the card does damage, show the number;
    # otherwise show "NO DMG". `{card.damage:2d}` formats the int as at
    # least 2 characters wide (right-aligned), so "DMG  8" and "DMG 18"
    # line up nicely.
    damage_str = f"DMG {card.damage:2d}" if card.damage else "NO DMG"

    # Long strings can be split across lines inside parentheses.
    # Python treats everything inside () as one expression.
    # `{pet.name:<10}` pads the name to 10 chars, LEFT-aligned (< means left).
    line = (
        f"  {pet.name:<10} plays "
        f"[{name_col}| {card_type_tag} | Tier {card.speed_tier} | {damage_str}]"
    )
    print(line)
    # The outer quotes are single ('), the inner quotes are double (") so
    # they don't conflict. Both ' and " work for strings in Python.
    print(f'    "{flavor}"')


def print_intuition_swap(pet: Pet, glimpsed_card: AbilityCard, new_card: AbilityCard) -> None:
    print(
        f"  ** {pet.name} glimpsed {glimpsed_card.name} "
        f"— swapped to {new_card.name}! **"
    )


def print_resolution(
    attacker: Pet,
    defender: Pet,
    card: AbilityCard,
    damage: int,
    effect_msg: str | None,
    tier_note: str,
) -> None:
    card_name = card.name
    print(f"  >> {attacker.name}'s {card_name} resolves{tier_note}")
    if damage > 0:
        print(f"     {defender.name} takes {damage} damage.  [{defender.name} HP: {defender.hp}/{defender.max_hp}]")
    if effect_msg:
        # Check which HP to show based on the effect type.
        # `"drains" in effect_msg` tests whether the substring "drains"
        # appears anywhere in effect_msg. `in` works on strings and lists.
        if "drains" in effect_msg:
            # Drain heals the attacker, so show the attacker's HP.
            print(f"     {effect_msg}  [{attacker.name} HP: {attacker.hp}/{attacker.max_hp}]")
        else:
            # Shield and stun don't change HP — just print the message.
            print(f"     {effect_msg}")
    if damage == 0 and not effect_msg:
        print("     No effect.")


def print_stun_skip(pet: Pet) -> None:
    print(f"  {pet.name} is stunned and cannot act this turn!")


def print_turn_end(pet_a: Pet, pet_b: Pet) -> None:
    # This function exists so the engine has a clean hook to call,
    # even if right now all it does is print a blank line. Easy to
    # expand later (e.g. show both HP bars after every turn).
    print()


def print_battle_result(winner: Pet | None, loser: Pet | None, turns: int) -> None:
    print()
    print(_SEP)
    # `winner is None` checks if winner is the None object specifically.
    # For None checks, `is None` / `is not None` is preferred over `== None`.
    if winner is None:
        print(f"  DRAW — Maximum turns ({turns}) reached.")
        if loser is not None:
            pass  # both pets listed by caller
    else:
        hp_str = f"{loser.hp}/{loser.max_hp}" if loser else "?"
        print(f"  BATTLE OVER — Turn {turns}")
        print(f"  WINNER: {winner.name}  ({loser.name} HP reached 0)")
    print(_SEP)


def print_personality_update(pet: Pet) -> None:
    # Importing inside a function is valid Python. It delays the import
    # until this function is actually called. Fine for rarely-used modules.
    import json

    p = pet.personality
    print(f"  {pet.name}'s updated personality:")

    # `json.dumps(obj)` serialises a Python dict/list to a JSON string.
    # indent=None keeps it on one line. indent=2 would pretty-print it.
    print(f"    {json.dumps(p.to_dict(), indent=None)}")

    # `if p.traits` is truthy if the list is non-empty.
    # An empty list [] is falsy; a list with any items is truthy.
    if p.traits:
        print(f"  {pet.name}'s traits: {p.traits}")
    print()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _print_pet_stats(pet: Pet) -> None:
    # Format spec reference (inside {}):
    #   :<10   left-align, pad to 10 chars
    #   :3d    right-align integer, minimum 3 chars wide
    # These keep columns lined up regardless of name/number length.
    print(
        f"  {pet.name:<10} — "
        f"HP: {pet.hp:3d}  ATK: {pet.attack:3d}  "
        f"DEF: {pet.defense:3d}  SPD: {pet.speed:3d}  INT: {pet.intuition:3d}"
    )
