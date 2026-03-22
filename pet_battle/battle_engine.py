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

# `import X as alias` lets you use a shorter name. Here we import the whole
# cli module so we can call cli.print_battle_header() etc. This makes it
# clear at the call site that the function comes from cli.py.
import pet_battle.cli as cli

# Module-level constant — the max turns before declaring a draw.
# Putting it here (not buried in a function) makes it easy to find and tweak.
_MAX_TURNS = 30

# A special "do nothing" card injected when a pet has every card on cooldown.
# It's a module-level constant because it's shared and never changed.
_REST = AbilityCard(
    name="Rest", damage=0, speed_tier=2, card_type="defensive", cooldown=0
)


class BattleEngine:
    # __init__ is the constructor — it runs when you write BattleEngine(...).
    # We store the four arguments as instance attributes (self.pet_a etc.)
    # so that run_battle() can access them later.
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
        # Local aliases — shorter names for things we'll use repeatedly.
        # `pet_a = self.pet_a` doesn't copy the object; both names point
        # to the same Pet in memory.
        pet_a, pet_b = self.pet_a, self.pet_b

        # An empty list that we'll append TurnRecord objects to as we go.
        # Type hint `list[TurnRecord]` is for your IDE / type checker.
        log: list[TurnRecord] = []

        cli.print_battle_header(pet_a, pet_b)

        # `range(1, _MAX_TURNS + 1)` produces 1, 2, 3, ... 30.
        # +1 because range's end is exclusive (it stops *before* the end).
        for turn in range(1, _MAX_TURNS + 1):
            cli.print_turn_header(turn)

            # --- Step 1: available cards ---
            # pet.available_cards() returns a list. If it's empty (all on
            # cooldown), `or [_REST]` kicks in. In Python, an empty list is
            # *falsy*, so `[] or [_REST]` evaluates to [_REST].
            avail_a = pet_a.available_cards() or [_REST]
            avail_b = pet_b.available_cards() or [_REST]

            # --- Step 2: LLM selection ---
            # We give each LLM only a *snapshot* of the enemy — name and HP,
            # nothing about what card they're about to play. This simulates
            # simultaneous selection: neither side gets to react to the other.
            snap_a = {"name": pet_a.name, "hp": pet_a.hp, "max_hp": pet_a.max_hp}
            snap_b = {"name": pet_b.name, "hp": pet_b.hp, "max_hp": pet_b.max_hp}

            # Handle stun: a stunned pet is forced to Rest.
            # We clear the stunned flag immediately so it only lasts one turn.
            if pet_a.stunned:
                cli.print_stun_skip(pet_a)
                # Tuple assignment: card_a gets _REST, flavor_a gets the string.
                card_a, flavor_a = _REST, f"{pet_a.name} is stunned and skips."
                pet_a.stunned = False
            else:
                # The LLM returns a (card, flavor) tuple; we unpack it directly.
                card_a, flavor_a = self.llm_a.choose_card(pet_a, avail_a, snap_b)

            if pet_b.stunned:
                cli.print_stun_skip(pet_b)
                card_b, flavor_b = _REST, f"{pet_b.name} is stunned and skips."
                pet_b.stunned = False
            else:
                card_b, flavor_b = self.llm_b.choose_card(pet_b, avail_b, snap_a)

            # --- Step 3: Intuition check ---
            # Each pet might swap their card if they "glimpse" the enemy's pick.
            # _intuition_check returns (possibly_new_card, did_swap).
            card_a, swapped_a = _intuition_check(pet_a, card_a, card_b, avail_a)
            card_b, swapped_b = _intuition_check(pet_b, card_b, card_a, avail_b)

            # Print selections after potential swaps so the output shows the
            # final choice, not the original one.
            cli.print_card_selection(pet_a, card_a, flavor_a, swapped_a)
            cli.print_card_selection(pet_b, card_b, flavor_b, swapped_b)
            print()  # blank line between selections and resolution

            # --- Step 4: Resolve by speed tier ---
            # _resolution_order returns a list of (attacker, defender, card)
            # tuples sorted so faster cards come first.
            order = _resolution_order(
                (pet_a, card_a), (pet_b, card_b)
            )

            # Tuple unpacking in a for loop — each iteration gives us three
            # separate variables instead of one tuple.
            for attacker, defender, card in order:
                _apply_card(attacker, defender, card)

                # Check win condition immediately after each card — a fast
                # card can end the battle before the slow one even fires.
                if defender.hp <= 0:
                    _record_turn(log, turn, card_a, card_b, flavor_a, flavor_b,
                                 pet_a, pet_b, swapped_a, swapped_b)
                    cli.print_turn_end(pet_a, pet_b)
                    cli.print_battle_result(attacker, defender, turn)
                    # `return` exits the entire method immediately, skipping
                    # the rest of the loop and all remaining turns.
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

        # If the for loop completes without returning, it's a draw.
        cli.print_battle_result(None, None, _MAX_TURNS)
        print(f"  {pet_a.name} HP: {pet_a.hp}/{pet_a.max_hp}   {pet_b.name} HP: {pet_b.hp}/{pet_b.max_hp}")
        return BattleResult(winner=None, loser=None, turns=_MAX_TURNS, battle_log=log,
                            pet_a=pet_a, pet_b=pet_b)


# ---------------------------------------------------------------------------
# Module-level helper functions
# ---------------------------------------------------------------------------
# These start with _ (underscore) by convention, signalling they're "private"
# — intended to be used only within this module, not imported elsewhere.
# Python doesn't enforce this, it's just a hint to other programmers.

def _intuition_check(
    pet: Pet,
    chosen: AbilityCard,
    enemy_card: AbilityCard,
    available: list[AbilityCard],
) -> tuple[AbilityCard, bool]:
    """Return (final_card, swapped). May swap chosen for a faster counter."""
    # Convert intuition (1–10) to a probability (0.05–0.50).
    # intuition=7 → 7/20 = 0.35, so a 35% chance to glimpse per turn.
    glimpse_prob = pet.intuition / 20.0

    # `random.random()` returns a float between 0.0 and 1.0 uniformly.
    # If it's >= the probability threshold, the glimpse fails → no swap.
    if random.random() >= glimpse_prob:
        return chosen, False

    # The pet glimpsed the enemy's card. Now look for a faster counter.
    # List comprehension with TWO conditions joined by `and`:
    #   - speed_tier must be strictly lower (faster) than the enemy's card
    #   - must not be the card we already chose (`is not` checks identity)
    faster = [
        c for c in available
        if c.speed_tier < enemy_card.speed_tier and c is not chosen
    ]

    if not faster:
        return chosen, False  # glimpsed but had nothing better to play

    # `max(iterable, key=fn)` finds the item for which fn returns the highest
    # value. `lambda c: c.damage` is an anonymous function that takes a card
    # and returns its damage — we use it to find the hardest-hitting counter.
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
    # Unpack each pair into named variables — cleaner than pair_a[0].
    pet_a, card_a = pair_a
    pet_b, card_b = pair_b

    # Build a list of tuples that bundle everything needed for sorting AND
    # for returning the final result. We include speed tier and pet speed
    # as the first two elements so `.sort()` can compare them.
    #
    # `-pet_a.speed` is negated so that a HIGHER pet speed sorts EARLIER.
    # Python's sort is ascending by default (lowest first), and we want the
    # fastest pet to go first on ties, so we flip the sign.
    entries = [
        (card_a.speed_tier, -pet_a.speed, pet_a, pet_b, card_a),
        (card_b.speed_tier, -pet_b.speed, pet_b, pet_a, card_b),
    ]

    # `key=lambda x: (x[0], x[1])` tells sort to compare tuples by their
    # first element, then second on ties — just like alphabetical order
    # works letter by letter. Tuples compare element-by-element in Python.
    entries.sort(key=lambda x: (x[0], x[1]))

    # Build the final list using a list comprehension.
    # `e[2], e[3], e[4]` extracts attacker, defender, card from each entry.
    return [(e[2], e[3], e[4]) for e in entries]


def _apply_card(attacker: Pet, defender: Pet, card: AbilityCard) -> None:
    """Apply a card's damage and effect; print resolution lines."""
    damage = 0
    effect_msg = None
    tier_note = ""

    if card.damage > 0:
        # `//` is floor division — divides and rounds DOWN to the nearest int.
        # We use it so attack scaling produces whole numbers, not decimals.
        # Example: damage=18, attack=12 → 18*12//10 = 21 (not 21.6)
        raw = card.damage * attacker.attack // 10

        # `max(1, ...)` guarantees at least 1 damage — no attack ever does zero.
        damage = max(1, raw - defender.defense)

        defender.hp -= damage  # shorthand for: defender.hp = defender.hp - damage

        # Clamp hp to 0: `max(0, hp)` prevents hp going negative.
        # Negative HP would still end the battle, but 0 is cleaner to display.
        defender.hp = max(0, defender.hp)

    # Apply special effects based on the card's effect tag.
    # Using `==` compares VALUES. Using `is` would compare identity —
    # wrong for strings (use == for string comparisons, is for None checks).
    if card.effect == "shield":
        bonus = 3
        defender.defense += bonus
        effect_msg = f"{defender.name} gains +{bonus} DEF for 1 turn."
    elif card.effect == "drain" and damage > 0:
        # `//` again: steal half the damage dealt, rounded down.
        heal = damage // 2
        # `min(max_hp, ...)` caps HP so you can't overheal above maximum.
        attacker.hp = min(attacker.max_hp, attacker.hp + heal)
        effect_msg = f"{attacker.name} drains {heal} HP back."
    elif card.effect == "stun":
        defender.stunned = True
        effect_msg = f"{defender.name} is stunned next turn!"

    cli.print_resolution(attacker, defender, card, damage, effect_msg, tier_note)


def _tick_cooldowns(pet: Pet, played: AbilityCard) -> None:
    # `is not` checks that played is not the exact same object as _REST.
    # We don't want to put the _REST placeholder on cooldown — it's fake.
    if played is not _REST and played.cooldown > 0:
        pet.cooldowns[played.name] = played.cooldown

    # Tick down every OTHER card's cooldown by 1.
    # `list(pet.cooldowns)` creates a copy of the keys so we can safely
    # iterate while modifying the dict. Iterating a dict while changing it
    # raises a RuntimeError in Python — always copy keys first.
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
    # `list.append(item)` adds item to the end of the list in-place.
    # Because `log` is passed by reference (Python always passes objects
    # by reference, not by value), appending here changes the same list
    # that run_battle() is holding.
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
