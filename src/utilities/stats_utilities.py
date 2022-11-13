from poke_env.environment import Pokemon, Weather, Field, Status, PokemonType, Effect
from poke_env.data import NATURES
from typing import Union

STATUS_CONDITIONS = [Status.BRN, Status.FRZ, Status.PAR, Status.PSN, Status.SLP, Status.TOX]


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


def compute_stat_boost(pokemon: Pokemon, stat: str, boost: Union[int | None] = None) -> float:
    if stat not in list(pokemon.base_stats.keys()) and stat not in ["accuracy", "evasion"]:
        raise ValueError

    # The "hp" stat can't have boosts
    if stat == "hp":
        return 1

    if boost and -6 <= boost <= 6:
        boost_to_apply = boost
    else:
        boost_to_apply = pokemon.boosts[stat]

    if stat not in ["accuracy, evasion"]:
        if boost_to_apply > 0:
            stat_boost = (2 + boost_to_apply) / 2
        else:
            stat_boost = 2 / (2 - boost_to_apply)
    else:
        if boost_to_apply > 0:
            stat_boost = (3 + boost_to_apply) / 3
        else:
            stat_boost = 3 / (3 - boost_to_apply)

    return round(stat_boost, 2)


def __compute_atk_modifiers(pokemon: Pokemon, weather: Weather = None) -> float:
    atk_modifier = 1

    if pokemon.ability == "flowergift" and weather in [Weather.SUNNYDAY, Weather.DESOLATELAND]:
        atk_modifier *= 1.5

    if pokemon.ability == "defeatist" and pokemon.current_hp_fraction <= 0.5:
        atk_modifier /= 0.5

    if pokemon.ability == "guts" and pokemon.status in STATUS_CONDITIONS:
        atk_modifier *= 1.5

    if pokemon.ability == "hustle":
        atk_modifier *= 1.5

    if pokemon.ability == "gorillatactics" and not pokemon.is_dynamaxed:
        atk_modifier *= 1.5

    if pokemon.ability in ["hugepower", "purepower"]:
        atk_modifier *= 2

    if pokemon.item == "choiceband" and not pokemon.is_dynamaxed:
        atk_modifier *= 1.5

    if pokemon.species in ["cubone", "marowak", "marowakalola"] and pokemon.item == "thickclub":
        atk_modifier *= 2

    if "pikachu" in pokemon.species and pokemon.item == "lightball":
        atk_modifier *= 2

    return atk_modifier


def __compute_def_modifiers(pokemon: Pokemon, terrains: list[Field] = None) -> float:
    def_modifier = 1

    if terrains and pokemon.ability == "grasspelt" and Field.GRASSY_TERRAIN in terrains:
        def_modifier *= 1.5

    if pokemon.ability == "marvelscale" and pokemon.status in STATUS_CONDITIONS:
        def_modifier *= 1.5

    # The "eviolite" item works with only non-fully evolved pokèmon, we assume that this item is used only for such case
    if pokemon.item == "eviolite":
        def_modifier *= 1.5

    if pokemon.species == "ditto" and pokemon.item == "metalpowder":
        def_modifier *= 2

    return def_modifier


def __compute_spa_modifiers(pokemon: Pokemon, weather: Weather = None) -> float:
    spa_modifier = 1

    if pokemon.ability in ["flowergift", "solarpower"] and weather in [Weather.SUNNYDAY, Weather.DESOLATELAND]:
        spa_modifier *= 1.5

    if pokemon.item == "choicespecs" and not pokemon.is_dynamaxed:
        spa_modifier *= 1.5

    if pokemon.species == "clamperl" and pokemon.item == "deepseatooth":
        spa_modifier *= 2

    if "pikachu" in pokemon.species and pokemon.item == "lightball":
        spa_modifier *= 2

    return spa_modifier


def __compute_spd_modifiers(pokemon: Pokemon, weather: Weather = None) -> float:
    spd_modifier = 1

    if PokemonType.ROCK in pokemon.types and weather is Weather.SANDSTORM:
        spd_modifier *= 1.5

    if pokemon.item == "assaultvest":
        spd_modifier *= 1.5

    if pokemon.species == "clamperl" and pokemon.item == "deepseascale":
        spd_modifier *= 2

    # The "eviolite" item works with only non-fully evolved pokèmon, we assume that this item is used only for such case
    if pokemon.item == "eviolite":
        spd_modifier *= 1.5

    if pokemon.species == "ditto" and pokemon.item == "metalpowder":
        spd_modifier *= 2

    return spd_modifier


def __compute_spe_modifiers(pokemon: Pokemon, weather: Weather = None, terrains: list[Field] = None) -> float:
    spe_modifier = 1

    if pokemon.ability == "swiftswim" and weather in [Weather.RAINDANCE, Weather.PRIMORDIALSEA]:
        spe_modifier *= 2

    if pokemon.ability == "chlorophyll" and weather in [Weather.SUNNYDAY, Weather.DESOLATELAND]:
        spe_modifier *= 2

    if pokemon.ability == "sandrush" and weather is Weather.SANDSTORM:
        spe_modifier *= 2

    if pokemon.ability == "slushrush" and weather is Weather.HAIL:
        spe_modifier *= 2

    if pokemon.ability == "quickfeet" and pokemon.status in STATUS_CONDITIONS:
        spe_modifier *= 1.5

    if terrains and pokemon.ability == "surgesurfer" and Field.ELECTRIC_TERRAIN in terrains:
        spe_modifier *= 2

    if pokemon.item == "choicescarf":
        spe_modifier *= 1.5

    if pokemon.species == "ditto" and pokemon.item == "quickpowder":
        spe_modifier *= 1.5

    if pokemon.item == "heavyball":
        spe_modifier *= 0.5

    if pokemon.status is Status.PAR:
        spe_modifier *= 0.5

    return spe_modifier


def __compute_accuracy_modifiers(pokemon: Pokemon) -> float:
    accuracy_modifier = 1

    if pokemon.ability == "compoundeyes":
        accuracy_modifier *= 1.3

    if pokemon.item == "widelens":
        accuracy_modifier *= 1.1

    if pokemon.item == "victorystar":
        accuracy_modifier *= 1.1

    return accuracy_modifier


def __compute_evasion_modifiers(pokemon: Pokemon, weather: Weather = None) -> float:
    evasion_modifier = 1

    if pokemon.ability == "sandveil" and weather is Weather.SANDSTORM:
        evasion_modifier *= 1.2

    if pokemon.ability == "tangledfeet" and Effect.CONFUSION in list(pokemon.effects.keys()):
        evasion_modifier *= 1.5

    if pokemon.ability == "snowcloak" and weather is Weather.HAIL:
        evasion_modifier *= 1.2

    if pokemon.item == "brigthpowder":
        evasion_modifier *= 1.1

    if pokemon.item == "laxincense":
        evasion_modifier *= 1.05

    return evasion_modifier


def compute_stat_modifiers(pokemon: Pokemon, stat: str, weather: Weather = None, terrains: list[Field] = None) -> float:
    match stat:
        case "atk":
            return __compute_atk_modifiers(pokemon, weather)
        case "def":
            return __compute_def_modifiers(pokemon, terrains)
        case "spa":
            return __compute_spa_modifiers(pokemon, weather)
        case "spd":
            return __compute_spd_modifiers(pokemon, weather)
        case "spe":
            return __compute_spe_modifiers(pokemon, weather, terrains)
        case "accuracy":
            return __compute_accuracy_modifiers(pokemon)
        case "evasion":
            return __compute_evasion_modifiers(pokemon, weather)

    return 1


def compute_stat(pokemon: Pokemon,
                 stat: str,
                 weather: Weather = None,
                 terrains: list[Field] = None,
                 is_bot: bool = False,
                 ivs: int = 31,
                 evs: int = 21,
                 nature: str = "Neutral") -> int:
    if is_bot and stat != "hp":
        stat_value = pokemon.stats[stat]
    else:
        stat_value = estimate_stat(pokemon, stat, ivs, evs, nature)

    modifiers = compute_stat_modifiers(pokemon, stat, weather, terrains)
    boost = compute_stat_boost(pokemon, stat)
    stat_value *= modifiers
    stat_value *= boost
    return int(stat_value)


def stats_to_string(pokemon: Pokemon,
                    stats: list[str],
                    weather: Weather = None,
                    terrains: list[Field] = None,
                    is_bot: bool = False) -> str:
    stats_string = ""
    for i, stat in enumerate(stats):
        stats_string += "{0:3}: {1:3}".format(stat, str(compute_stat(pokemon, stat, weather, terrains, is_bot)))
        if i != len(stats) - 1:
            stats_string += " "

    return stats_string
