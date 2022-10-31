from poke_env.environment import Pokemon, Move, Weather, Field, Status
from poke_env.environment.move_category import MoveCategory
from poke_env.data import NATURES
from poke_env.environment.pokemon_type import PokemonType


def estimate_stat(pokemon: Pokemon, stat: str, ivs: int = 31, evs: int = 21, nature: str = "Neutral") -> int:
    estimated_stat = 2 * pokemon.base_stats[stat] + ivs + evs
    estimated_stat = int(estimated_stat * pokemon.level / 100) + 5

    # The hp stat has a different computation than the others
    if stat == "hp":
        if pokemon.species == "shedinja":
            return 1

        estimated_stat = estimated_stat + pokemon.level + 5
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


def __compute_other_damage_multipliers(move: Move, attacker: Pokemon, defender: Pokemon) -> float:
    damage_multiplier = 1

    # Pokèmon with the guts ability that have a serious status condition deal 1.5 more damage
    status_conditions = [Status.BRN, Status.FRZ, Status.PAR, Status.PSN, Status.SLP, Status.TOX]
    if attacker.status in status_conditions and attacker.ability == "guts":
        damage_multiplier = damage_multiplier * 1.5

    # Pokèmon with the water absorb ability suffer no damage from water type moves
    if move.type is PokemonType.WATER and defender.ability == "waterabsorb":
        return 0

    # Pokèmon with the volt absorb ability suffer no damage from electric type moves
    if move.type is PokemonType.ELECTRIC and defender.ability == "voltabsorb":
        return 0

    # Pokèmon with the flash fire ability suffer no damage from fire type moves
    if move.type is PokemonType.FIRE and defender.ability == "flashfire":
        return 0

    # Pokèmon with the wonder guard ability can only take damage from super-effective moves
    if defender.ability == "wonderguard" and defender.damage_multiplier(move) < 2:
        return 0

    # Pokèmon with the rivalry ability deal 1.25 more damage to pokèmon of the same gender,
    # while dealing 0.75 less damage to the ones from the opposite gender
    if attacker.ability == "rivalry":
        if attacker.gender == defender.gender:
            damage_multiplier = damage_multiplier * 1.25
        else:
            damage_multiplier = 0.75

    # Pokèmon with one of the following abilities deal 1.5 more damage if their current hp is less or equal than 1/3
    if attacker.ability in ["overgrow", "blaze", "torrent", "swarm"] and attacker.current_hp_fraction <= 0.33:
        damage_multiplier = damage_multiplier * 1.5

    # Pokèmon with the sheer force ability deal 1.3 more damage, but their moves have no secondary beneficiary effect
    if attacker.ability == "sheerforce":
        damage_multiplier = damage_multiplier * 1.3

    if "darkaura" in [attacker.ability, defender.ability] and move.type is PokemonType.DARK:
        if "aurabreak" not in [attacker.ability, defender.ability]:
            damage_multiplier = damage_multiplier * 1.33
        else:
            damage_multiplier = damage_multiplier * 0.75

    if "fairyaura" in [attacker.ability, defender.ability] and move.type is PokemonType.FAIRY:
        if "aurabreak" not in [attacker.ability, defender.ability]:
            damage_multiplier = damage_multiplier * 1.33
        else:
            damage_multiplier = damage_multiplier * 0.75

    if attacker.ability == "dragonsmaw" and move.type is PokemonType.DRAGON:
        damage_multiplier = damage_multiplier * 1.5

    if attacker.ability == "transistor" and move.type is PokemonType.ELECTRIC:
        damage_multiplier = damage_multiplier * 1.5

    if attacker.ability in ["steelworker", "steelyspirit"] and move.type is PokemonType.STEEL:
        damage_multiplier = damage_multiplier * 1.5

    if defender.ability in ["filter", "solidrock", "prismarmor"] and defender.damage_multiplier(move) >= 2:
        damage_multiplier = damage_multiplier * 0.75

    if defender.ability in ["multiscale", "shadowshield"] and defender.current_hp_fraction == 1:
        damage_multiplier = damage_multiplier * 0.5

    if attacker.ability == "neuroforce" and defender.damage_multiplier(move) >= 2:
        damage_multiplier = damage_multiplier * 1.25

    if attacker.ability == "reckless" and move.recoil > 0:
        damage_multiplier = damage_multiplier * 1.2

    if attacker.ability == "technician" and move.base_power <= 60:
        damage_multiplier = damage_multiplier * 1.5

    # Pokèmon that held the life orb item deal 1.1 damage
    if attacker.item == "lifeorb":
        damage_multiplier = damage_multiplier * 1.1

    return damage_multiplier


def compute_damage(move: Move,
                   attacker: Pokemon,
                   defender: Pokemon,
                   weather_list: list,
                   field_list: list,
                   is_bot: bool) -> int:
    if move.category is MoveCategory.STATUS:
        return 0

    if move.damage > 0:
        return move.damage

    move_type = move.type

    # Compute the effect of the attacker level
    level_multiplier = 2 * attacker.level / 5 + 2

    # Compute the ratio between the attacker atk/spa stat and the defender def/spd stat
    if move.category is MoveCategory.PHYSICAL:
        boosts_to_consider = ["atk", "def"]
        if is_bot:
            attack_stat = attacker.stats["atk"]
            defense_stat = estimate_stat(defender, "def")
        else:
            attack_stat = estimate_stat(attacker, "atk")
            defense_stat = defender.stats["def"]
    else:
        boosts_to_consider = ["spa", "spd"]
        if is_bot:
            attack_stat = attacker.stats["spa"]
            defense_stat = estimate_stat(defender, "spd")
        else:
            attack_stat = estimate_stat(attacker, "spa")
            defense_stat = defender.stats["spd"]

    if defender.ability != "unaware":
        attack_stat = attack_stat * compute_stat_boost(attacker, boosts_to_consider[0])

    if attacker.ability != "unaware":
        defense_stat = defense_stat * compute_stat_boost(defender, boosts_to_consider[1])

    ratio_attack_defense = attack_stat / defense_stat
    print("Move under evaluation: {0}".format(move.id))
    print("Pokemon: {0}, {1} Attack: {2}".format(attacker.species, move.category.name, int(attack_stat)))
    print("Pokemon: {0}, Appr. {1} Defense: {2}".format(defender.species, move.category.name, int(defense_stat)))

    # Compute the base damage before taking into account any modifier
    damage = level_multiplier * move.base_power * ratio_attack_defense / 50 + 2

    # Compute the effect of the weather
    weather_multiplier = 1
    if len(weather_list) > 0 and not ["airlock", "cloudnine"] in [attacker.ability, defender.ability]:
        weather = weather_list[0]
        if weather in [Weather.SUNNYDAY, Weather.DESOLATELAND]:
            if move_type is PokemonType.FIRE:
                weather_multiplier = 1.5
            elif move_type is PokemonType.WATER:
                weather_multiplier = 0.5
                if weather is Weather.DESOLATELAND:
                    return 0
        elif weather in [Weather.RAINDANCE, Weather.PRIMORDIALSEA]:
            if move_type is PokemonType.WATER:
                weather_multiplier = 1.5
            elif move_type is PokemonType.FIRE:
                weather_multiplier = 0.5
                if weather is Weather.PRIMORDIALSEA:
                    return 0

    damage = damage * weather_multiplier

    # Compute the effect of the field
    field_multiplier = 1
    if len(field_list) > 0:
        field = field_list[0]
        if field is Field.ELECTRIC_TERRAIN:
            if move_type is PokemonType.ELECTRIC:
                field_multiplier = 1.3
        elif field is Field.GRASSY_TERRAIN:
            if move_type is PokemonType.GRASS:
                field_multiplier = 1.3
            elif move.id in ["earthquake", "magnitude", "bulldoze"]:
                field_multiplier = 0.5
        elif field is Field.MISTY_TERRAIN:
            if move_type is PokemonType.DRAGON:
                field_multiplier = 0.5
        elif field is Field.PSYCHIC_TERRAIN:
            if move_type is PokemonType.PSYCHIC:
                field_multiplier = 1.3
            elif move.priority > 0:
                return 0

    damage = damage * field_multiplier

    # Compute the effect of the STAB
    if move_type in attacker.types:
        if attacker.ability == "adaptability":
            stab_multiplier = 2
        else:
            stab_multiplier = 1.5
    else:
        stab_multiplier = 1

    damage = damage * stab_multiplier

    # Compute the effect of the burn
    if attacker.status is Status.BRN and move.category is MoveCategory.PHYSICAL and attacker.ability != "guts":
        damage = damage * 0.5

    # Compute the effect of the defender's types
    type_multiplier = defender.damage_multiplier(move)
    damage = damage * type_multiplier

    # Compute the effect of various abilities and items
    other_damage_multipliers = __compute_other_damage_multipliers(move, attacker, defender)
    damage = int(damage * other_damage_multipliers)
    print("Damage: {0}\n".format(damage))
    return damage


def can_out_speed_pokemon(bot_pokemon: Pokemon, opponent_pokemon: Pokemon) -> float:
    # Retrieve the bot pokèmon speed
    bot_pokemon_speed = bot_pokemon.stats["spe"]

    # Estimate the lower and higher bound for the opponent pokèmon speed, assume that ivs are 31 for both cases
    opponent_pokemon_speed_lower = estimate_stat(opponent_pokemon, "spe", evs=0)
    opponent_pokemon_speed_higher = estimate_stat(opponent_pokemon, "spe", evs=64)

    # Compute the boost to the stat if there are any
    bot_pokemon_speed = int(bot_pokemon_speed * compute_stat_boost(bot_pokemon, "spe"))
    opponent_pokemon_speed_boost = compute_stat_boost(opponent_pokemon, "spe")
    opponent_pokemon_speed_lower = int(opponent_pokemon_speed_lower * opponent_pokemon_speed_boost)
    opponent_pokemon_speed_higher = int(opponent_pokemon_speed_higher * opponent_pokemon_speed_boost)

    if bot_pokemon_speed < opponent_pokemon_speed_lower:
        return 0
    elif bot_pokemon_speed > opponent_pokemon_speed_higher:
        return 1
    else:
        prob_out_speed = (bot_pokemon_speed - opponent_pokemon_speed_lower) / 64
        return prob_out_speed
