from poke_env.environment import Pokemon, Weather, Field, Status, PokemonType, Effect
from poke_env.data import NATURES
from src.engine.useful_data import STATUS_CONDITIONS
from typing import Union, List


def estimate_stat(pokemon: Pokemon, stat: str, ivs: int = 31, evs: int = 84, nature: str = "neutral") -> int:
    """
    Estimate the stat of a Pokémon without considering boosts and modifiers. This method should be used only for
    estimating the stats of the opponent's Pokémon since you can know your active Pokémon stats by using the attribute
    with the same name. The method will not work for the "accuracy" and "evasion" stats
    :param pokemon: the Pokémon under consideration
    :param stat: the stat we want to estimate
    :param ivs: individual values for the stat
    :param evs: effort values for the stat
    :param nature: the Pokémon's nature
    :return: an estimation of a Pokémon's stat
    """
    if stat not in list(pokemon.base_stats.keys()) and stat not in ["accuracy", "evasion"]:
        raise ValueError

    if ivs < 0 or ivs > 31 or evs < 0 or evs > 252:
        raise ValueError

    estimated_stat = 2 * pokemon.base_stats[stat] + ivs + evs / 4
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
        if nature != "neutral":
            if nature not in NATURES.keys():
                raise ValueError

            estimated_stat = int(estimated_stat * NATURES[nature][stat])

    return estimated_stat


def compute_stat_boost(pokemon: Pokemon, stat: str, boost: Union[int | None] = None) -> float:
    """
    Compute the boost to a Pokémon stat. This method computes the actual boost and not the number of stages,
    for the latter you can just use the "boosts" attribute of a Pokémon object. The method will not work for the
    "accuracy" and "evasion" stats
    :param pokemon: the Pokémon under consideration
    :param stat: the stat we are considering
    :param boost: the stages we can force on the stat boost computation
    :return: the modifier to the stat that comes from its boosts
    """
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

    # Pokémon with the "flower gift" ability have their attack increased under sunny weather
    if pokemon.ability == "flowergift" and weather in [Weather.SUNNYDAY, Weather.DESOLATELAND]:
        atk_modifier *= 1.5

    # Pokémon with the "defeatist" ability have their attack halved when their hp is <= 1/2
    if pokemon.ability == "defeatist" and pokemon.current_hp_fraction <= 0.5:
        atk_modifier *= 0.5

    # Pokémon with the "guts" ability have their attack increased when they have a status condition
    if pokemon.ability == "guts" and pokemon.status in STATUS_CONDITIONS:
        atk_modifier *= 1.5

    # Pokémon with the "hustle" ability have their attack increased
    if pokemon.ability == "hustle":
        atk_modifier *= 1.5

    # Pokémon with the "gorilla tactics" have their attack increased if they are not dynamaxed
    if pokemon.ability == "gorillatactics" and not pokemon.is_dynamaxed:
        atk_modifier *= 1.5

    # Pokémon with the "huge power" or "pure power" abilities have their attack doubled
    if pokemon.ability in ["hugepower", "purepower"]:
        atk_modifier *= 2

    # Pokémon with the "choiceband" item have their attack increased
    if pokemon.item == "choiceband" and not pokemon.is_dynamaxed:
        atk_modifier *= 1.5

    # Cubone and its evolutions have their attack doubled if they hold the "thick club" item
    if pokemon.species in ["cubone", "marowak", "marowakalola"] and pokemon.item == "thickclub":
        atk_modifier *= 2

    # Pikachu has its attack doubled if it holds the "light ball" item
    if "pikachu" in pokemon.species and pokemon.item == "lightball":
        atk_modifier *= 2

    return atk_modifier


def __compute_def_modifiers(pokemon: Pokemon, terrains: List[Field] = None) -> float:
    def_modifier = 1

    # Pokémon with the "grass pelt" ability have their defense increased under grassy terrain
    if pokemon.ability == "grasspelt" and Field.GRASSY_TERRAIN in terrains:
        def_modifier *= 1.5

    # Pokémon with the "marvel scale" ability have their defense increased if they have a status condition
    if pokemon.ability == "marvelscale" and pokemon.status in STATUS_CONDITIONS:
        def_modifier *= 1.5

    # The "eviolite" item works with only non-fully evolved pokèmon, we assume that this item is used only in such case
    if pokemon.item == "eviolite":
        def_modifier *= 1.5

    # Ditto has its defense doubled if it holds the "metal powder" item
    if pokemon.species == "ditto" and pokemon.item == "metalpowder":
        def_modifier *= 2

    return def_modifier


def __compute_spa_modifiers(pokemon: Pokemon, weather: Weather = None) -> float:
    spa_modifier = 1

    # Pokémon with the "flower gift" or "solar power" abilities have their special attack increased under sunny weather
    if pokemon.ability in ["flowergift", "solarpower"] and weather in [Weather.SUNNYDAY, Weather.DESOLATELAND]:
        spa_modifier *= 1.5

    # Pokémon with the "choice specs" item have their special attack increased if not dynmaxed
    if pokemon.item == "choicespecs" and not pokemon.is_dynamaxed:
        spa_modifier *= 1.5

    # Clamperl has its special attack doubled if it holds the "deep sea tooth" item
    if pokemon.species == "clamperl" and pokemon.item == "deepseatooth":
        spa_modifier *= 2

    # Pikachu has its special attack doubled if it holds the "light ball" item
    if "pikachu" in pokemon.species and pokemon.item == "lightball":
        spa_modifier *= 2

    return spa_modifier


def __compute_spd_modifiers(pokemon: Pokemon, weather: Weather = None) -> float:
    spd_modifier = 1

    # Rock-type Pokémon have their special defense increased under sandstorm
    if PokemonType.ROCK in pokemon.types and weather is Weather.SANDSTORM:
        spd_modifier *= 1.5

    # Pokémon with the "assault vest" item have their special defense increased
    if pokemon.item == "assaultvest":
        spd_modifier *= 1.5

    # Clamperls has its special defense increased if it holds the "deep sea scale" item
    if pokemon.species == "clamperl" and pokemon.item == "deepseascale":
        spd_modifier *= 2

    # The "eviolite" item works with only non-fully evolved pokèmon, we assume that this item is used only for such case
    if pokemon.item == "eviolite":
        spd_modifier *= 1.5

    # Ditto has its special defense doubled if it holds the "metal powder" item
    if pokemon.species == "ditto" and pokemon.item == "metalpowder":
        spd_modifier *= 2

    return spd_modifier


def __compute_spe_modifiers(pokemon: Pokemon, weather: Weather = None, terrains: List[Field] = None) -> float:
    spe_modifier = 1

    # Pokémon with the "swift swim" ability have their speed doubled under rainy weather
    if pokemon.ability == "swiftswim" and weather in [Weather.RAINDANCE, Weather.PRIMORDIALSEA]:
        spe_modifier *= 2

    # Pokémon with the "chlorophyll" ability have their speed doubled under sunny day
    if pokemon.ability == "chlorophyll" and weather in [Weather.SUNNYDAY, Weather.DESOLATELAND]:
        spe_modifier *= 2

    # Pokémon with the "sand rush" ability have their speed doubled under sandstorm
    if pokemon.ability == "sandrush" and weather is Weather.SANDSTORM:
        spe_modifier *= 2

    # Pokémon with the "slush rush" ability have their speed doubled under hail
    if pokemon.ability == "slushrush" and weather is Weather.HAIL:
        spe_modifier *= 2

    # Pokémon with the "quick feet" ability have their speed increased if they have a status condition
    if pokemon.ability == "quickfeet" and pokemon.status in STATUS_CONDITIONS:
        spe_modifier *= 1.5

    # Pokémon with the "surge surfer" ability have their speed doubled under electric terrain
    if pokemon.ability == "surgesurfer" and Field.ELECTRIC_TERRAIN in terrains:
        spe_modifier *= 2

    # Pokémon with the "choice scarf" item have their speed increased
    if pokemon.item == "choicescarf":
        spe_modifier *= 1.5

    # Ditto has its speed increased if it holds the "quick powder" item
    if pokemon.species == "ditto" and pokemon.item == "quickpowder":
        spe_modifier *= 1.5

    # Pokémon with the "heavy ball" item have their speed halved
    if pokemon.item == "heavyball":
        spe_modifier *= 0.5

    # Paralyzed Pokémon have their speed halved
    if pokemon.status is Status.PAR:
        spe_modifier *= 0.5

    return spe_modifier


def __compute_accuracy_modifiers(pokemon: Pokemon) -> float:
    accuracy_modifier = 1

    # Pokémon with the "compound eyes" have their accuracy increased
    if pokemon.ability == "compoundeyes":
        accuracy_modifier *= 1.3

    # Pokémon with the "wide lens" item have their accuracy increased
    if pokemon.item == "widelens":
        accuracy_modifier *= 1.1

    # Pokémon with the "victory star" item have their accuracy increased
    if pokemon.item == "victorystar":
        accuracy_modifier *= 1.1

    return accuracy_modifier


def __compute_evasion_modifiers(pokemon: Pokemon, weather: Weather = None) -> float:
    evasion_modifier = 1

    # Pokémon with the "sand veil" ability have their evasion increased under sandstorm
    if pokemon.ability == "sandveil" and weather is Weather.SANDSTORM:
        evasion_modifier *= 1.2

    # Pokémon with the "tangled feet" ability have their evasion increased if they are confused
    if pokemon.ability == "tangledfeet" and Effect.CONFUSION in list(pokemon.effects.keys()):
        evasion_modifier *= 1.5

    # Pokémon with the "snow cloak" ability have their evasion increased under hail
    if pokemon.ability == "snowcloak" and weather is Weather.HAIL:
        evasion_modifier *= 1.2

    # Pokémon with the "bright powder" item have their evasion increased
    if pokemon.item == "brigthpowder":
        evasion_modifier *= 1.1

    # Pokémon with the "lax incense" item have their evasion increased
    if pokemon.item == "laxincense":
        evasion_modifier *= 1.05

    return evasion_modifier


def compute_stat_modifiers(pokemon: Pokemon, stat: str, weather: Weather = None, terrains: List[Field] = None) -> float:
    """
    Compute all the modifiers for a Pokémon's stat coming from abilities, items, weather and terrains
    :param pokemon: the Pokémon under consideration
    :param stat: the stat under consideration
    :param weather: the current weather
    :param terrains: the current terrains on the field
    :return: the modifier to a Pokémon's stat
    """
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
                 terrains: List[Field] = None,
                 is_bot: bool = False,
                 ivs: int = 31,
                 evs: int = 84,
                 boost: int = None,
                 nature: str = "neutral") -> int:
    """
    Compute the stat ("atk", "def", "spa", "spd", "spe", "accuracy", "evasion") of a Pokémon
    :param pokemon: the Pokémon under consideration
    :param stat: the stat we want to compute
    :param weather: the current weather
    :param terrains: the current terrains on the field
    :param is_bot: if the Pokémon belongs to the bot
    :param ivs: individual values for the stat
    :param evs: effort values for the stat
    :param boost: boost's stages for the stat
    :param nature: the Pokémon's nature
    :return: the actual stat value by taking into account the boost and all the modifiers
    """
    if ivs < 0 or ivs > 31 or evs < 0 or evs > 252:
        raise ValueError

    if stat in ["accuracy", "evasion"]:
        stat_value = 1
    elif is_bot and stat != "hp":
        stat_value = pokemon.stats[stat]
    else:
        stat_value = estimate_stat(pokemon, stat, ivs, evs, nature)

    modifiers = compute_stat_modifiers(pokemon, stat, weather, terrains)
    boost = compute_stat_boost(pokemon, stat, boost)
    stat_value *= modifiers
    stat_value *= boost
    if stat not in ["accuracy", "evasion"]:
        stat_value = int(stat_value)

    return stat_value


def stats_to_string(pokemon: Pokemon,
                    stats: List[str],
                    weather: Weather = None,
                    terrains: List[Field] = None,
                    is_bot: bool = False) -> str:
    """
    Builds a String with all the Pokémon's stats by computing their actual value
    :param pokemon: the Pokémon under consideration
    :param stats: the stats we want to consider
    :param weather: the current weather
    :param terrains: the current terrains on the field
    :param is_bot: if the Pokémon belongs to the bot
    :return: String with all the desired stats and their actual values
    """
    stats_string = ""
    for i, stat in enumerate(stats):
        stats_string += "{0:3}: {1:3}".format(stat, str(compute_stat(pokemon, stat, weather, terrains, is_bot)))
        if i != len(stats) - 1:
            stats_string += " "

    return stats_string
