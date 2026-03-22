"""
Pretty-print helpers for turn-by-turn battle output.
All formatting lives here; battle_engine.py just calls these functions.
"""
from __future__ import annotations
from pet_battle.models import AbilityCard, Pet

_SEP = "=" * 60
_CARD_NAME_WIDTH = 16


def print_battle_header(pet_a: Pet, pet_b: Pet) -> None:
    print(_SEP)
    print(f"  BATTLE: {pet_a.name} vs. {pet_b.name}")
    print(_SEP)
    _print_pet_stats(pet_a)
    _print_pet_stats(pet_b)
    print(_SEP)
    print()


def print_turn_header(turn: int) -> None:
    print(f"--- Turn {turn} ---")


def print_card_selection(pet: Pet, card: AbilityCard, flavor: str, swapped: bool) -> None:
    card_type_tag = card.card_type[:3].upper()
    name_col = card.name.ljust(_CARD_NAME_WIDTH)
    damage_str = f"DMG {card.damage:2d}" if card.damage else "NO DMG"
    line = (
        f"  {pet.name:<10} plays "
        f"[{name_col}| {card_type_tag} | Tier {card.speed_tier} | {damage_str}]"
    )
    print(line)
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
        # drain heals the attacker; shield/stun affect the defender but don't change HP shown here
        if "drains" in effect_msg:
            print(f"     {effect_msg}  [{attacker.name} HP: {attacker.hp}/{attacker.max_hp}]")
        else:
            print(f"     {effect_msg}")
    if damage == 0 and not effect_msg:
        print("     No effect.")


def print_stun_skip(pet: Pet) -> None:
    print(f"  {pet.name} is stunned and cannot act this turn!")


def print_turn_end(pet_a: Pet, pet_b: Pet) -> None:
    print()


def print_battle_result(winner: Pet | None, loser: Pet | None, turns: int) -> None:
    print()
    print(_SEP)
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
    import json
    p = pet.personality
    print(f"  {pet.name}'s updated personality:")
    print(f"    {json.dumps(p.to_dict(), indent=None)}")
    if p.traits:
        print(f"  {pet.name}'s traits: {p.traits}")
    print()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _print_pet_stats(pet: Pet) -> None:
    print(
        f"  {pet.name:<10} — "
        f"HP: {pet.hp:3d}  ATK: {pet.attack:3d}  "
        f"DEF: {pet.defense:3d}  SPD: {pet.speed:3d}  INT: {pet.intuition:3d}"
    )
