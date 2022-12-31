from poke_env.environment import Pokemon, Move, Status, Effect
from poke_env.environment.move_category import MoveCategory
from poke_env.environment.pokemon_type import PokemonType
from src.engine.useful_data import STATUS_CONDITIONS, IGNORE_EFFECT_ABILITIES_IDS
from src.engine.stats import compute_stat
from typing import Union


def base_power_modifiers_moves(move: Move, attacker: Pokemon, defender: Pokemon) -> float:
    """
    Computes the modifiers of a move's base power considering the move itself.
    :param move: move under consideration
    :param attacker: attacking pokémon
    :param defender: defending pokémon
    :return: Base power modifier that takes into account abilities and items
        """
    base_power_modifier = 1

    # The power of the move "facade" is doubled if the user has a status condition
    if move.id == "facade" and attacker.status in STATUS_CONDITIONS:
        base_power_modifier *= 2

    # The power of the move "brine" is doubled if the user has no item
    if move.id == "acrobatics" and attacker.item is None:
        base_power_modifier *= 2

    # The power of the move "brine" is doubled if the user hp is <= 1/2
    if move.id == "brine" and attacker.current_hp_fraction <= 0.5:
        base_power_modifier *= 2

    # The power of the move "venoshock" is doubled if the defender is poisoned
    if move.id == "venoshock" and defender.status in [Status.PSN, Status.TOX]:
        base_power_modifier *= 2

    if move.id == "gravapple" and Effect.GRAVITY in defender.effects:
        base_power_modifier *= 2

    # The power of the move "hex" is doubled if the defending pokémon has a status condition
    if move.id == "hex" and defender.status in STATUS_CONDITIONS:
        base_power_modifier *= 2

    return base_power_modifier


def base_power_modifiers_abilities(move: Move, move_type: PokemonType, attacker: Pokemon, defender: Pokemon) -> float:
    """
    Computes the modifiers of a move's base power considering the abilities of both active pokémon.
    :param move: move under consideration
    :param move_type: move type
    :param attacker: attacking pokémon
    :param defender: defending pokémon
    :return: Base power modifier that takes into account abilities and items
    """
    base_power_modifier = 1

    if "neutralizinggas" in [attacker.ability, defender.ability]:
        return 1

    # Moves of pokémon with the following abilities have their power increased if their hp is less or equal than 1/3
    if attacker.current_hp_fraction <= 0.33:
        if attacker.ability == "overgrow" and move_type is PokemonType.GRASS:
            base_power_modifier *= 1.5

        if attacker.ability == "blaze" and move_type is PokemonType.FIRE:
            base_power_modifier *= 1.5

        if attacker.ability == "torrent" and move_type is PokemonType.WATER:
            base_power_modifier *= 1.5

        if attacker.ability == "swarm" and move_type is PokemonType.BUG:
            base_power_modifier *= 1.5

    # The "reckless" ability boosts power of moves with recoil
    if attacker.ability == "reckless" and move.recoil > 0:
        base_power_modifier *= 1.2

    # The "iron fist" ability boosts power of punching moves
    if attacker.ability == "ironfist" and "punch" in move.flags:
        base_power_modifier *= 1.2

    # The "normalize" ability changes all move types to normal-type and boosts their power
    if attacker.ability == "normalize" and move_type is not PokemonType.NORMAL:
        base_power_modifier *= 1.2

    # The "aerilate" ability changes all normal-type moves to flying-type and boosts their power
    if attacker.ability == "aerilate" and move_type is PokemonType.NORMAL:
        base_power_modifier *= 1.2

    # The "refrigerate" ability changes all normal-type moves to ice-type and boosts their power
    if attacker.ability == "refrigerate" and move_type is PokemonType.NORMAL:
        base_power_modifier *= 1.2

    # The "pixilate" ability changes all normal-type moves to fairy-type and boosts their power
    if attacker.ability == "pixilate" and move_type is PokemonType.NORMAL:
        base_power_modifier *= 1.2

    # The "galvanize" ability changes all normal-type moves to electric-type and boosts their power
    if attacker.ability == "galvanize" and move_type is PokemonType.NORMAL:
        base_power_modifier *= 1.2

    # The "water bubble" ability doubles the power of water-type moves
    if attacker.ability == "waterbubble" and move_type is PokemonType.WATER:
        base_power_modifier *= 2

    # The "punk rock" ability boosts the power of sound-based moves
    if attacker.ability == "punkrock" and "sound" in move.flags:
        base_power_modifier *= 1.3

    # If a pokémon with the "dark aura" ability is active, the power of dark-type moves is increased
    if "darkaura" in [attacker.ability, defender.ability] and move_type is PokemonType.DARK:
        # If a pokémon with the "aura break" ability is active, the power of dark-type moves is decreased
        if "aurabreak" not in [attacker.ability, defender.ability]:
            base_power_modifier *= 1.33
        elif attacker.ability not in IGNORE_EFFECT_ABILITIES_IDS:
            base_power_modifier *= 0.75

    # If a pokémon with the "fairy aura" ability is active, the power of fairy-type moves is increased
    if "fairyaura" in [attacker.ability, defender.ability] and move_type is PokemonType.FAIRY:
        # If a pokémon with the "aura break" ability is active, the power of fairy-type moves is decreased
        if "aurabreak" not in [attacker.ability, defender.ability]:
            base_power_modifier *= 1.33
        elif attacker.ability not in IGNORE_EFFECT_ABILITIES_IDS:
            base_power_modifier *= 0.75

    # The "strong jaw" ability boosts the power of biting moves
    if attacker.ability == "strongjaw" and "bite" in move.flags:
        base_power_modifier *= 1.5

    # The "mega-launcher" ability boosts the power of aura and pulse moves
    if attacker.ability == "megalauncher" and "pulse" in move.flags:
        base_power_modifier *= 1.5

    # The "technician" ability boosts the power of moves with a base power <= 60
    if attacker.ability == "technician" and move.base_power <= 60:
        base_power_modifier *= 1.5

    # The "toxic boost" ability boosts the power of physical moves if the user is poisoned
    if attacker.ability == "toxicboost" and move.category is MoveCategory.PHYSICAL \
            and attacker.status in [Status.PSN, Status.TOX]:
        base_power_modifier *= 1.5

    # The "flare boost" ability boosts the power of special moves if the user is burned
    if attacker.ability == "flareboost" and move.category is MoveCategory.SPECIAL and attacker.status in [Status.BRN]:
        base_power_modifier *= 1.5

    # The "dragon's maw" ability boosts the power of dragon-type moves
    if attacker.ability == "dragonsmaw" and move_type is PokemonType.DRAGON:
        base_power_modifier *= 1.5

    # The "transistor" ability boosts the power of electric-type moves
    if attacker.ability == "transistor" and move_type is PokemonType.ELECTRIC:
        base_power_modifier *= 1.5

    # The "steelworker" and "steely spirit" abilities boost the power of steel-type moves
    if attacker.ability in ["steelworker", "steelyspirit"] and move_type is PokemonType.STEEL:
        base_power_modifier *= 1.5

    return base_power_modifier


def base_power_modifiers_items(move: Move, move_type: PokemonType, attacker: Pokemon) -> float:
    """
    Computes the modifiers of a move's base power considering the items of the active pokémon.
    :param move: move under consideration
    :param move_type: move type
    :param attacker: attacking pokémon
    :return: Base power modifier that takes into account abilities and items
    """
    if attacker.item is None or attacker.item == "unknown_item":
        return 1

    base_power_modifier = 1

    # The "muscleband" item boosts the power of physical moves
    if attacker.item == "muscleband" and move.category is MoveCategory.PHYSICAL:
        base_power_modifier *= 1.1

    # The "wise glasses" item boosts the power of special moves
    if attacker.item == "wiseglasses" and move.category is MoveCategory.SPECIAL:
        base_power_modifier *= 1.1

    # The "black belt" item boosts the power of fighting-type moves
    if attacker.item == "blackbelt" and move_type is PokemonType.FIGHTING:
        base_power_modifier *= 1.2

    # The "black glasses" item boosts the power of dark-type moves
    if attacker.item == "blackglasses" and move_type is PokemonType.DARK:
        base_power_modifier *= 1.2

    # The "charcoal" item boosts the power of fire-type moves
    if attacker.item == "charcoal" and move_type is PokemonType.FIRE:
        base_power_modifier *= 1.2

    # The "dragon fang" item boosts the power of dragon-type moves
    if attacker.item == "dragonfang" and move_type is PokemonType.DRAGON:
        base_power_modifier *= 1.2

    # The "hard stone" item boosts the power of rock-type moves
    if attacker.item == "hardstone" and move_type is PokemonType.ROCK:
        base_power_modifier *= 1.2

    # The "magnet" item boosts the power of electric-type moves
    if attacker.item == "magnet" and move_type is PokemonType.ELECTRIC:
        base_power_modifier *= 1.2

    # The "metal coat" item boosts the power of steel-type moves
    if attacker.item == "metalcoat" and move_type is PokemonType.STEEL:
        base_power_modifier *= 1.2

    # The "miracle seed" item boosts the power of grass-type moves
    if attacker.item == "miracleseed" and move_type is PokemonType.GRASS:
        base_power_modifier *= 1.2

    # The "mystic water" item boosts the power of water-type moves
    if attacker.item == "mysticwater" and move_type is PokemonType.WATER:
        base_power_modifier *= 1.2

    # The "never-melt ice" item boosts the power of ice-type moves
    if attacker.item == "nevermeltice" and move_type is PokemonType.ICE:
        base_power_modifier *= 1.2

    # The "poison barb" item boosts the power of poison-type moves
    if attacker.item == "poisonbarb" and move_type is PokemonType.POISON:
        base_power_modifier *= 1.2

    # The "sharp beek" item boosts the power of flying-type moves
    if attacker.item == "sharpbeek" and move_type is PokemonType.FLYING:
        base_power_modifier *= 1.2

    # The "silkscarf" item boosts the power of normal-type moves
    if attacker.item == "slikscarf" and move_type is PokemonType.NORMAL:
        base_power_modifier *= 1.2

    # The "silver powder" item boosts the power of bug-type moves
    if attacker.item == "silverpowder" and move_type is PokemonType.BUG:
        base_power_modifier *= 1.2

    # The "soft sand" item boosts the power of ground-type moves
    if attacker.item == "softsand" and move_type is PokemonType.GROUND:
        base_power_modifier *= 1.2

    # The "spell tag" item boosts the power of ghost-type moves
    if attacker.item == "spelltag" and move_type is PokemonType.GHOST:
        base_power_modifier *= 1.2

    # The "twisted spoon" item boosts the power of psychic-type moves
    if attacker.item == "twistedspoon" and move_type is PokemonType.PSYCHIC:
        base_power_modifier *= 1.2

    return base_power_modifier


def compute_base_power(move: Move,
                       move_type: PokemonType,
                       attacker: Pokemon,
                       defender: Pokemon,
                       modifier: bool = False) -> Union[float, int]:
    """
    Compute the base power of a move considering the move itself, the abilities of both active pokémon and their items.
    :param move: move under consideration
    :param move_type: the current type of the move
    :param attacker: attacking pokémon
    :param defender: defending pokémon
    :param modifier: if the modifier is given instead of the actual base power
    :return: the actual base power or the modifier
    """
    power = move.base_power

    # Some moves change their power based on the attacker's remaining hp
    if move.id in ["eruption", "waterspout", "dragonenergy"]:
        attacker_max_hp = compute_stat(attacker, "hp")
        attacker_current_hp = int(attacker_max_hp * attacker.current_hp_fraction)
        power = int(150 * attacker_current_hp / attacker_max_hp)
        if power < 1:
            power = 1

    # The "grass knot" move has its power based on the defender's weight
    if move.id == "grassknot":
        defender_weight = defender.weight
        if defender_weight < 10:
            power = 20
        elif defender_weight < 25:
            power = 40
        elif defender_weight < 50:
            power = 60
        elif defender_weight < 100:
            power = 80
        elif defender_weight < 200:
            power = 100
        else:
            power = 120

    # Some move have their power increased by the amount of the user's positive boosts
    if move.id in ["powertrip", "storedpower"]:
        boosts = sum([boost for boost in attacker.boosts.values() if boost > 0])
        power = 20 * (boosts + 1)

    # Compute all modifiers
    base_power_modifier = base_power_modifiers_moves(move, attacker, defender)
    base_power_modifier *= base_power_modifiers_abilities(move, move_type, attacker, defender)
    base_power_modifier *= base_power_modifiers_items(move, move_type, attacker)

    if modifier:
        return base_power_modifier
    else:
        return int(power * base_power_modifier)
