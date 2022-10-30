from poke_env.environment import Pokemon, Move, Weather, Field, Status
from poke_env.environment.move_category import MoveCategory


def _compute_boost_to_stat(pokemon: Pokemon, stat: str) -> float:
    if pokemon.boosts[stat] > 0:
        stat_boost = (2 + pokemon.boosts[stat]) / 2
    else:
        stat_boost = 2 / (2 - pokemon.boosts[stat])

    return stat_boost


def compute_damage(move: Move,
                   attacker: Pokemon,
                   defender: Pokemon,
                   weather_list: list,
                   field_list: list,
                   is_bot: bool) -> int:
    if move.category is MoveCategory.STATUS:
        return 0

    move_type = move.type

    # Compute the effect of the attacker level
    level_multiplier = 2 * attacker.level / 5 + 2

    # Compute the ratio between the attacker atk/spa stat and the defender def/spd stat
    if move.category is MoveCategory.PHYSICAL:
        boosts_to_consider = ["atk", "def"]
        if is_bot:
            attack_stat = attacker.stats["atk"]
            defense_stat = defender.base_stats["def"]
        else:
            attack_stat = attacker.base_stats["atk"]
            defense_stat = defender.stats["def"]
    else:
        boosts_to_consider = ["spa", "spd"]
        if is_bot:
            attack_stat = attacker.stats["spa"]
            defense_stat = defender.base_stats["spd"]
        else:
            attack_stat = attacker.base_stats["spa"]
            defense_stat = defender.stats["spd"]

    if is_bot:
        defense_stat = 2 * defense_stat + 31  # assume max IVs
        defense_stat = defense_stat + 21  # assume that EVs are spread equally between all the stats
        defense_stat = defense_stat * defender.level / 100 + 5  # assume that the nature is neutral
    else:
        attack_stat = 2 * attack_stat + 31  # assume max IVs
        attack_stat = attack_stat + 21  # assume that EVs are spread equally between all the stats
        attack_stat = attack_stat * attacker.level / 100 + 5  # assume that nature is neutral

    attack_stat = attack_stat * _compute_boost_to_stat(attacker, boosts_to_consider[0])
    defense_stat = defense_stat * _compute_boost_to_stat(defender, boosts_to_consider[1])
    ratio_attack_defense = attack_stat / defense_stat
    print("Move under evaluation: {0}".format(move.id))
    print("Pokemon: {0}, {1} Attack: {2}".format(attacker.species, move.category.name, int(attack_stat)))
    print("Pokemon: {0}, Appr. {1} Defense: {2}".format(defender.species, move.category.name, int(defense_stat)))

    # Compute the base damage before taking into account any modifier
    damage = level_multiplier * move.base_power * ratio_attack_defense / 50 + 2

    # Compute the effect of the weather
    weather_multiplier = 1
    if len(weather_list) > 0:
        weather = weather_list[0]
        if weather in [Weather.SUNNYDAY, Weather.DESOLATELAND]:
            if move_type == "Fire":
                weather_multiplier = 1.5
            elif move_type == "Water":
                weather_multiplier = 0.5
                if weather is Weather.DESOLATELAND:
                    return 0
        elif weather in [Weather.RAINDANCE, Weather.PRIMORDIALSEA]:
            if move_type == "Water":
                weather_multiplier = 1.5
            elif move_type == "Fire":
                weather_multiplier = 0.5
                if weather is Weather.PRIMORDIALSEA:
                    return 0

    damage = damage * weather_multiplier

    # Compute the effect of the field
    field_multiplier = 1
    if len(field_list) > 0:
        field = field_list[0]
        if field is Field.ELECTRIC_TERRAIN:
            if move_type == "Electric":
                field_multiplier = 1.3
        elif field is Field.GRASSY_TERRAIN:
            if move_type == "Grass":
                field_multiplier = 1.3
            elif move.id in ["earthquake", "magnitude", "bulldoze"]:
                field_multiplier = 0.5
        elif field is Field.MISTY_TERRAIN:
            if move_type == "Dragon":
                field_multiplier = 0.5
        elif field is Field.PSYCHIC_TERRAIN:
            if move_type == "Psychic":
                field_multiplier = 1.3
            elif move.priority > 0:
                return 0

    damage = damage * field_multiplier

    # Compute effect of the STAB
    if move_type in attacker.types:
        if attacker.ability == "Adaptability":
            stab_multiplier = 2
        else:
            stab_multiplier = 1.5
    else:
        stab_multiplier = 1

    damage = damage * stab_multiplier

    # Compute the effect of the burn
    if attacker.status is Status.BRN and move.category is MoveCategory.PHYSICAL and attacker.ability != "Guts":
        damage = damage * 0.5

    # Compute the effect of the defender's types
    type_multiplier = defender.damage_multiplier(move)
    damage = int(damage * type_multiplier)
    print("Damage: {0}\n".format(damage))
    return damage
