from poke_env.environment import Pokemon, Move, Weather, Field, Status
from poke_env.data import NATURES


def estimate_stat(pokemon: Pokemon, stat: str, ivs: int = 31, evs: int = 21, nature: str = "Neutral") -> int:
    estimated_stat = 2 * pokemon.base_stats[stat] + ivs + evs
    estimated_stat = int(estimated_stat * pokemon.level / 100) + 5

    # The hp stat has a different computation than the others
    if stat == "hp":
        if pokemon.species == "shedinja":
            return 1

        estimated_stat += pokemon.level + 5
        if pokemon.is_dynamaxed:
            estimated_stat *= 2
    else:
        # Compute nature multiplier
        if nature != "Neutral":
            estimated_stat = int(estimated_stat * NATURES[nature][stat])

    return estimated_stat


def compute_stat_boost(pokemon: Pokemon, stat: str) -> float:
    if pokemon.boosts[stat] > 0:
        stat_boost = (2 + pokemon.boosts[stat]) / 2
    else:
        stat_boost = 2 / (2 - pokemon.boosts[stat])

    return stat_boost


def __compute_atk_modifiers(pokemon: Pokemon,
                            weather: Weather = None,
                            terrain: Field = None,
                            is_bot: bool = False) -> float:
    atk_modifier = 1
    return atk_modifier


def __compute_def_modifiers(pokemon: Pokemon,
                           weather: Weather = None,
                           terrain: Field = None,
                           is_bot: bool = False) -> float:
    def_modifier = 1
    return def_modifier


def __compute_spa_modifiers(pokemon: Pokemon,
                            weather: Weather = None,
                            terrain: Field = None,
                            is_bot: bool = False) -> float:
    spa_modifier = 1
    return spa_modifier


def __compute_spd_modifiers(pokemon: Pokemon,
                            weather: Weather = None,
                            terrain: Field = None,
                            is_bool: bool = False) -> float:
    spd_modifier = 1
    return spd_modifier


def __compute_spe_modifiers(pokemon: Pokemon,
                            weather: Weather = None,
                            terrain: Field = None,
                            is_bool: bool = False) -> float:
    spe_modifier = 1
    return spe_modifier


def compute_stat_modifiers(pokemon: Pokemon,
                           stat: str,
                           weather: Weather = None,
                           terrain: Field = None,
                           is_bot: bool = False) -> float:
    match stat:
        case "atk":
            return __compute_atk_modifiers(pokemon, weather, terrain, is_bot)
        case "def":
            return __compute_def_modifiers(pokemon, weather, terrain, is_bot)
        case "spa":
            return __compute_spa_modifiers(pokemon, weather, terrain, is_bot)
        case "spd":
            return __compute_spd_modifiers(pokemon, weather, terrain, is_bot)
        case "spe":
            return __compute_spe_modifiers(pokemon, weather, terrain, is_bot)

    return 1
