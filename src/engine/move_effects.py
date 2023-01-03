from typing import List
from poke_env.environment import Pokemon, Move, Weather, Field
from poke_env.environment.pokemon_type import PokemonType
from src.engine.useful_data import STATUS_CONDITIONS, HEALING_MOVES
from src.engine.stats import estimate_stat, compute_stat


def move_changes_type(move: Move, attacker: Pokemon) -> (bool, PokemonType):
    """
    Computes the new type of the move if the attacker has an ability or item that changes it.
    :param move: the move under consideration
    :param attacker: the pokémon
    :return: Boolean that states if the move has changed type and the new type itself
    """
    move_type = move.type

    # The "normalize" ability changes all move types to normal-type and boosts their power
    if attacker.ability == "normalize" and move_type is not PokemonType.NORMAL:
        move_type = PokemonType.NORMAL

    # The "aerilate" ability changes all normal-type moves to flying-type and boosts their power
    if attacker.ability == "aerilate" and move_type is PokemonType.NORMAL:
        move_type = PokemonType.FLYING

    # The "refrigerate" ability changes all normal-type moves to ice-type and boosts their power
    if attacker.ability == "refrigerate" and move_type is PokemonType.NORMAL:
        move_type = PokemonType.ICE

    # The "pixilate" ability changes all normal-type moves to fairy-type and boosts their power
    if attacker.ability == "pixilate" and move_type is PokemonType.NORMAL:
        move_type = PokemonType.FAIRY

    # The "liquid voide" ability changes all sound-based moves to water-type
    if attacker.ability == "liquidvoice" and "sound" in move.flags:
        move_type = PokemonType.WATER

    # Some moves change type by effect of the attacker ability and held item
    if attacker.ability in ["multitype", "rkssystem"] and attacker.item:
        if attacker.ability == "multitype" and move.id == "judgement" and attacker.item[-5:] == "plate":
            move_type = PokemonType.from_name(attacker.item[:-5])

        if attacker.ability == "rkssystem" and move.id == "multiattack" and attacker.item[-6:] == "memory":
            move_type = PokemonType.from_name(attacker.item[:-6])

    if move_type is not move.type:
        return True, move_type
    else:
        return False, move.type


def compute_healing(attacker: Pokemon,
                    defender: Pokemon,
                    move: Move,
                    weather: Weather = None,
                    terrains: List[Field] = None,
                    is_bot: bool = False) -> (int, float):
    """
    Compute the healing dealt by a move.
    :param attacker: attacking pokémon
    :param defender: defending pokémon
    :param move: move under consideration
    :param weather: current battle weather
    :param terrains: current battle terrains
    :param is_bot: whether the pokémon belongs to the bot's team
    :return: Healing and healing percentage of the move
    """
    healing = None
    healing_percentage = 0.5
    if attacker.is_dynamaxed or move.id not in HEALING_MOVES:
        return 0, 0

    if is_bot:
        max_hp = attacker.max_hp
        current_hp = attacker.current_hp
    else:
        max_hp = compute_stat(attacker, "hp", weather, terrains)
        current_hp = int(max_hp * attacker.current_hp_fraction)

    if move.id in ["morningsun", "moonlight", "synthesis"]:
        if weather in [Weather.SUNNYDAY, Weather.DESOLATELAND]:
            healing_percentage = 0.66
        elif weather in [Weather.RAINDANCE, Weather.PRIMORDIALSEA, Weather.HAIL, Weather.SANDSTORM]:
            healing_percentage = 0.25

    # We assume that bot doesn't heal the opponent's pokémon from its status conditions
    if move.id == "purify" and attacker.status not in STATUS_CONDITIONS:
        return 0, 0

    if move.id == "rest":
        if Field.ELECTRIC_TERRAIN in terrains or Field.PSYCHIC_TERRAIN in terrains:
            return 0, 0

        healing = max_hp - current_hp
        healing_percentage = round(healing / max_hp, 2)
        return healing, healing_percentage

    if move.id == "shoreup" and weather is Weather.SANDSTORM:
        healing_percentage = 0.66

    if move.id == "strengthsap":
        # We assume that the target is the defender
        atk_boost = defender.boosts["atk"]
        if defender.ability == "contrary":
            atk_boost = atk_boost + 1 if atk_boost < 6 else 6
        elif atk_boost == -6:
            return 0, 0
        else:
            atk_boost = atk_boost - 1 if atk_boost > -6 else -6

        healing = compute_stat(defender, "atk", weather, terrains, not is_bot, boost=atk_boost)

    if healing is None:
        healing = int(max_hp * healing_percentage)

    healing = healing if current_hp + healing <= max_hp else max_hp - current_hp
    healing_percentage = round(healing / max_hp, 2)
    return healing, healing_percentage


def compute_drain(pokemon: Pokemon, move: Move, damage: int, is_bot: False) -> (int, float):
    """
    Compute the draining effect of a move.
    :param pokemon: attacking pokémon
    :param move: move under consideration
    :param damage: damage dealt by the move
    :param is_bot: whether the pokémon belongs to the bot's team
    :return: Drain and drain percentage dealt by the move
    """
    if move.drain == 0:
        return 0, 0

    if is_bot:
        max_hp = pokemon.max_hp
        current_hp = pokemon.current_hp
    else:
        max_hp = estimate_stat(pokemon, "hp")
        current_hp = max_hp * pokemon.current_hp_fraction

    drain = int(damage * move.drain)
    drain = drain if current_hp + drain <= max_hp else max_hp - current_hp
    drain_percentage = round(drain / max_hp, 2)
    return drain, drain_percentage


def compute_recoil(pokemon: Pokemon, move: Move, damage: int, is_bot: bool = False) -> int:
    """
    Computes the recoil dealt by a move.
    :param pokemon: attacking pokémon
    :param move: move under consideration
    :param damage: damage dealt by the move
    :param is_bot: whether the pokémon belongs to the bot's team
    :return: Recoil dealt by the move.
    """
    if move.recoil == 0 or pokemon.ability == "magicguard":
        return 0

    if is_bot:
        max_hp = pokemon.max_hp
    else:
        max_hp = estimate_stat(pokemon, "hp")

    if move.id in ["mindblown", "steelbeam"]:
        recoil = int(max_hp / 2)
    elif move.self_destruct:
        recoil = max_hp
    else:
        recoil = int(damage * move.recoil)

    return recoil
