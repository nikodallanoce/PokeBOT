from poke_env.environment import Pokemon, Move, Weather, Field, AbstractBattle
from poke_env.environment.move_category import MoveCategory
from src.engine.stats import compute_stat_modifiers, compute_stat_boost, compute_stat, stats_to_string
from src.utilities.utilities import types_to_string


def outspeed_prob(bot_pokemon: Pokemon,
                  opp_pokemon: Pokemon,
                  weather: Weather = None,
                  terrains: list[Field] = None,
                  boost: int = None,
                  verbose: bool = False) -> dict[str, float]:
    """
    Computes the probability of outspeeding the opponent's pokémon.

    :param bot_pokemon: bot's active pokémon
    :param opp_pokemon: opponent's active pokémon
    :param weather: current battle weather
    :param terrains: current battle terrains
    :param boost: bot's pokémon "spe" stat boost
    :param verbose: print the computations
    :return: Outspeed probability, lower and upper bound of the opponent's "spe" stat
    """
    # Compute the stats for both pokémon
    bot_spe = compute_stat(bot_pokemon, "spe", weather, terrains, True, boost=boost)
    opp_spe_lb = compute_stat(opp_pokemon, "spe", weather, terrains, evs=0, boost=boost)
    opp_spe_ub = compute_stat(opp_pokemon, "spe", weather, terrains, evs=63, boost=boost)
    if verbose:
        print("{0} spe: {1}, {2} spe: {3} {4}".format(bot_pokemon.species, bot_spe, opp_pokemon.species,
                                                      opp_spe_lb, opp_spe_ub))

    # Compute the outspeed probability
    if bot_spe < opp_spe_lb:
        outspeed_p = 0
    elif bot_spe > opp_spe_ub:
        outspeed_p = 1
    else:
        outspeed_p = (bot_spe - opp_spe_lb) / 63

    # If "trick room" is active then the priority given by the "spe" stat are inverted
    if Field.TRICK_ROOM in terrains:
        outspeed_p = 1 - outspeed_p

    return {"outspeed_p": round(outspeed_p, 2), "lb": opp_spe_lb, "ub": opp_spe_ub}


def compute_move_accuracy(move: Move,
                          attacker: Pokemon,
                          defender: Pokemon,
                          weather: Weather = None,
                          terrains: list[Field] = None,
                          attacker_accuracy_boost: int = None,
                          defender_evasion_boost: int = None,
                          verbose: bool = False) -> float:
    """
    Computes the accuracy of a move.

    :param move: move under consideration
    :param attacker: attacking pokémon
    :param defender: defending pokémon
    :param weather: current battle weather
    :param terrains: current battle terrains
    :param attacker_accuracy_boost: attacker's "accuracy" stat boost
    :param defender_evasion_boost: defender's "evasion" stat boost
    :param verbose: print the computations
    :return: The accuracy of the move.
    """
    # Some moves can't miss by effect of the move itself or the "no guard" ability
    if move.accuracy is True or attacker.is_dynamaxed or attacker.ability == "noguard":
        if verbose:
            print("Move {0} accuracy: {1}".format(move.id, 1))

        return 1

    accuracy = move.accuracy

    # The moves "thunder" and "hurricane" have different accuracies with respect to the active weather
    if move.id in ["thunder", "hurricane"]:
        if weather in [Weather.SUNNYDAY, Weather.DESOLATELAND]:
            accuracy = 0.5
        elif weather in [Weather.RAINDANCE, Weather.PRIMORDIALSEA]:
            return 1

    # The move "blizzard" has an accuracy of 1 if the weather is hail
    if move.id == "blizzard" and weather is Weather.HAIL:
        return 1

    # One-hit KO moves have their accuracy boosted by the difference between the attacker and defender levels
    if move.id in ["fissure", "guillotine", "horndrill", "sheercold"]:
        if defender.level <= attacker.level:
            accuracy += attacker.level - defender.level
        else:
            if verbose:
                print("Move {0} accuracy: {1}".format(move.id, accuracy))

            return move.accuracy

    # Apply modifiers to attacker's accuracy and defender's evasion
    accuracy *= compute_stat_modifiers(attacker, "accuracy", weather, terrains)
    evasion = compute_stat_modifiers(defender, "evasion", weather, terrains)

    # Compute boosts to the previous stats
    accuracy *= compute_stat_boost(attacker, "accuracy", attacker_accuracy_boost)
    evasion *= compute_stat_boost(defender, "evasion", defender_evasion_boost)

    # Pokémon with the "hustle" ability have their accuracy decreased while using a physical move
    if attacker.ability == "hustle" and move.category is MoveCategory.PHYSICAL:
        accuracy *= 0.8

    # Compute move accuracy
    move_accuracy = accuracy / evasion

    if verbose:
        print("Move {0} accuracy: {1}".format(move.id, move_accuracy))

    return round(move_accuracy, 2)


def retrieve_battle_status(battle: AbstractBattle) -> dict:
    """
    Retrieves some infos about the current battle.

    :param battle: battle under consideration
    :return: Weather, terrains and conditions on both sides
    """
    # Retrieve weather and terrain
    weather = None if len(battle.weather.keys()) == 0 else next(iter(battle.weather.keys()))
    terrains = list(battle.fields.keys())

    # Retrieve conditions for both sides
    bot_conditions = list(battle.side_conditions.keys())
    opp_conditions = list(battle.opponent_side_conditions.keys())
    return {"weather": weather, "terrains": terrains, "bot_conditions": bot_conditions,
            "opp_conditions": opp_conditions}


def bot_status_to_string(bot_pokemon: Pokemon, opp_pokemon: Pokemon, weather: Weather, terrains: list[Field]) -> str:
    """
    Builds a string that contains the main infos of a battle turn from the bot's viewpoint.

    :param bot_pokemon: bot's pokémon
    :param opp_pokemon: opponent's pokémon
    :param weather: current battle weather
    :param terrains: current battle terrains
    :return: String with the most useful infos of the current battle turn
    """
    bot_max_hp = bot_pokemon.max_hp
    bot_hp = bot_pokemon.current_hp
    opp_max_hp = compute_stat(opp_pokemon, "hp", weather, terrains)
    opp_hp = int(opp_max_hp * opp_pokemon.current_hp_fraction)

    bot_status = "Bot pokémon: {0}, Types: {1}, hp: {2}/{3}\n"\
        .format(bot_pokemon.species, types_to_string(bot_pokemon.types), bot_hp, bot_max_hp)
    bot_status += "Ability: {0}, Item: {1}\n".format(bot_pokemon.ability, bot_pokemon.item)
    bot_stats = stats_to_string(bot_pokemon, list(bot_pokemon.stats.keys()), weather, terrains, True)
    bot_status += "Stats: {0}\n\n".format(bot_stats)

    bot_status += "Opponent pokèmon: {0}, Types: {1}, hp: {2}/{3}\n"\
        .format(opp_pokemon.species, types_to_string(opp_pokemon.types), opp_hp, opp_max_hp)
    if opp_pokemon.ability:
        opp_abilities = "Ability: {0}".format(opp_pokemon.ability)
    else:
        opp_abilities = "Possible abilities: {0}".format(opp_pokemon.possible_abilities)

    bot_status += "{0}, Item: {1}\n".format(opp_abilities, opp_pokemon.item)
    opp_stats = stats_to_string(opp_pokemon, list(opp_pokemon.stats.keys()), weather, terrains)
    bot_status += "Stats: {0}\n\n".format(opp_stats)
    bot_status += "Weather: {0}, Terrains: {1}".format(weather, terrains)
    return bot_status
