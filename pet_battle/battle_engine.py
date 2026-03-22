"""
BattleEngine — orchestrates the turn loop.

Responsibilities:
  - Collecting available cards each turn
  - Calling LLM backends for card selection (simultaneously, neither sees the other's pick)
  - Running the intuition check (glimpse + optional swap)
  - Resolving cards in speed-tier order
  - Applying effects: shield, drain, stun
  - Tracking cooldowns
  - Printing turn-by-turn output via cli.py
  - Returning a BattleResult
"""
from __future__ import annotations
import random
from pet_battle.models import AbilityCard, BattleResult, Pet, TurnRecord
from pet_battle.llm_interface import LLMBackend
import pet_battle.cli as cli

_MAX_TURNS = 30

# Free "Rest" card injected when a pet has all cards on cooldown
_REST = AbilityCard(
    name="Rest", damage=0, speed_tier=2, card_type="defensive", cooldown=0
)


class BattleEngine:
    def __init__(
        self,
        pet_a: Pet,
        pet_b: Pet,
        llm_a: LLMBackend,
        llm_b: LLMBackend,
    ) -> None:
        self.pet_a = pet_a
        self.pet_b = pet_b
        self.llm_a = llm_a
        self.llm_b = llm_b

    def run_battle(self) -> BattleResult:
        pet_a, pet_b = self.pet_a, self.pet_b
        log: list[TurnRecord] = []

        cli.print_battle_header(pet_a, pet_b)

        for turn in range(1, _MAX_TURNS + 1):
            cli.print_turn_header(turn)

            # --- Step 1: available cards ---
            avail_a = pet_a.available_cards() or [_REST]
            avail_b = pet_b.available_cards() or [_REST]

            # --- Step 2: LLM selection (simultaneous; enemy snapshot has no card info) ---
            snap_a = {"name": pet_a.name, "hp": pet_a.hp, "max_hp": pet_a.max_hp}
            snap_b = {"name": pet_b.name, "hp": pet_b.hp, "max_hp": pet_b.max_hp}

            # Handle stun
            if pet_a.stunned:
                cli.print_stun_skip(pet_a)
                card_a, flavor_a = _REST, f"{pet_a.name} is stunned and skips."
                pet_a.stunned = False
            else:
                card_a, flavor_a = self.llm_a.choose_card(pet_a, avail_a, snap_b)

            if pet_b.stunned:
                cli.print_stun_skip(pet_b)
                card_b, flavor_b = _REST, f"{pet_b.name} is stunned and skips."
                pet_b.stunned = False
            else:
                card_b, flavor_b = self.llm_b.choose_card(pet_b, avail_b, snap_a)

            # --- Step 3: Intuition check ---
            card_a, swapped_a = _intuition_check(pet_a, card_a, card_b, avail_a)
            card_b, swapped_b = _intuition_check(pet_b, card_b, card_a, avail_b)

            # Print selections (after potential swaps)
            cli.print_card_selection(pet_a, card_a, flavor_a, swapped_a)
            cli.print_card_selection(pet_b, card_b, flavor_b, swapped_b)
            print()

            # --- Step 4: Resolve by speed tier ---
            order = _resolution_order(
                (pet_a, card_a), (pet_b, card_b)
            )
            for attacker, defender, card in order:
                _apply_card(attacker, defender, card)

                # Win condition: check after each card resolves
                if defender.hp <= 0:
                    _record_turn(log, turn, card_a, card_b, flavor_a, flavor_b,
                                 pet_a, pet_b, swapped_a, swapped_b)
                    cli.print_turn_end(pet_a, pet_b)
                    cli.print_battle_result(attacker, defender, turn)
                    return BattleResult(
                        winner=attacker, loser=defender,
                        turns=turn, battle_log=log,
                        pet_a=pet_a, pet_b=pet_b,
                    )

            # --- Step 5: Apply cooldowns ---
            _tick_cooldowns(pet_a, card_a)
            _tick_cooldowns(pet_b, card_b)

            _record_turn(log, turn, card_a, card_b, flavor_a, flavor_b,
                         pet_a, pet_b, swapped_a, swapped_b)
            cli.print_turn_end(pet_a, pet_b)

        # Draw
        cli.print_battle_result(None, None, _MAX_TURNS)
        print(f"  {pet_a.name} HP: {pet_a.hp}/{pet_a.max_hp}   {pet_b.name} HP: {pet_b.hp}/{pet_b.max_hp}")
        return BattleResult(winner=None, loser=None, turns=_MAX_TURNS, battle_log=log,
                            pet_a=pet_a, pet_b=pet_b)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _intuition_check(
    pet: Pet,
    chosen: AbilityCard,
    enemy_card: AbilityCard,
    available: list[AbilityCard],
) -> tuple[AbilityCard, bool]:
    """Return (final_card, swapped). May swap chosen for a faster counter."""
    glimpse_prob = pet.intuition / 20.0
    if random.random() >= glimpse_prob:
        return chosen, False

    # Pet glimpsed the enemy's card — look for a faster counter
    faster = [
        c for c in available
        if c.speed_tier < enemy_card.speed_tier and c is not chosen
    ]
    if not faster:
        return chosen, False  # glimpsed but nothing better

    best = max(faster, key=lambda c: c.damage)
    print(f"  ** {pet.name} glimpsed {enemy_card.name} — swapped to {best.name}! **")
    return best, True


def _resolution_order(
    pair_a: tuple[Pet, AbilityCard],
    pair_b: tuple[Pet, AbilityCard],
) -> list[tuple[Pet, Pet, AbilityCard]]:
    """
    Returns [(attacker, defender, card), ...] sorted by speed tier ASC,
    then by pet.speed DESC as tiebreaker.
    """
    pet_a, card_a = pair_a
    pet_b, card_b = pair_b

    entries = [
        (card_a.speed_tier, -pet_a.speed, pet_a, pet_b, card_a),
        (card_b.speed_tier, -pet_b.speed, pet_b, pet_a, card_b),
    ]
    entries.sort(key=lambda x: (x[0], x[1]))
    return [(e[2], e[3], e[4]) for e in entries]


def _apply_card(attacker: Pet, defender: Pet, card: AbilityCard) -> None:
    """Apply a card's damage and effect; print resolution lines."""
    damage = 0
    effect_msg = None
    tier_note = ""

    if card.damage > 0:
        raw = card.damage * attacker.attack // 10
        damage = max(1, raw - defender.defense)
        defender.hp -= damage
        defender.hp = max(0, defender.hp)

    if card.effect == "shield":
        bonus = 3
        defender.defense += bonus  # raw defense; we'll leave cleanup to a future system
        effect_msg = f"{defender.name} gains +{bonus} DEF for 1 turn."
    elif card.effect == "drain" and damage > 0:
        heal = damage // 2
        attacker.hp = min(attacker.max_hp, attacker.hp + heal)
        effect_msg = f"{attacker.name} drains {heal} HP back."
    elif card.effect == "stun":
        defender.stunned = True
        effect_msg = f"{defender.name} is stunned next turn!"

    cli.print_resolution(attacker, defender, card, damage, effect_msg, tier_note)


def _tick_cooldowns(pet: Pet, played: AbilityCard) -> None:
    if played is not _REST and played.cooldown > 0:
        pet.cooldowns[played.name] = played.cooldown
    for name in list(pet.cooldowns):
        if name != played.name:
            pet.cooldowns[name] = max(0, pet.cooldowns[name] - 1)


def _record_turn(
    log: list[TurnRecord],
    turn: int,
    card_a: AbilityCard,
    card_b: AbilityCard,
    flavor_a: str,
    flavor_b: str,
    pet_a: Pet,
    pet_b: Pet,
    swapped_a: bool,
    swapped_b: bool,
) -> None:
    log.append(TurnRecord(
        turn_number=turn,
        pet_a_card=card_a,
        pet_b_card=card_b,
        pet_a_flavor=flavor_a,
        pet_b_flavor=flavor_b,
        pet_a_hp_after=pet_a.hp,
        pet_b_hp_after=pet_b.hp,
        swapped_a=swapped_a,
        swapped_b=swapped_b,
        pet_a_card_type=card_a.card_type,
        pet_b_card_type=card_b.card_type,
    ))
