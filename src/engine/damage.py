from poke_env.environment import Pokemon, Move, Weather, Field, Status, SideCondition, PokemonGender, Effect
from poke_env.environment.move_category import MoveCategory
from poke_env.environment.pokemon_type import PokemonType
from src.engine.stats import compute_stat
from src.engine.base_power import compute_base_power
from src.engine.useful_data import IGNORE_EFFECT_ABILITIES_IDS
from src.engine.move_effects import move_changes_type
from typing import Union


def move_fixed_damage(move: Move, move_type: PokemonType, attacker: Pokemon, defender: Pokemon) -> (bool, int):
    """
    Computes the damage dealt by fixed-damage moves.
    :param move: move under consideration
    :param move_type: move type
    :param attacker: attacking pokémon
    :param defender: defending pokémon
    :return: Boolean that states if the move has a fixed damage and the damage itself
    """
    fixed_damage = None

    # Status moves deal no damage
    if move.category is MoveCategory.STATUS:
        fixed_damage = 0

    # Take care of moves that do fixed damage or equal to the attacker's level
    if type(move.damage) is not str:
        if move.damage > 0:
            fixed_damage = move.damage
    else:
        fixed_damage = attacker.level

    # One hit KO moves do as much damage as the remaining hp if the attacker's level is equal or higher
    # than the defender's, otherwise they deal no damage
    if move.id in ["fissure", "guillotine", "horndrill", "sheercold"]:
        if defender.level <= attacker.level and defender.damage_multiplier(move_type) > 0:
            fixed_damage = defender.current_hp
        else:
            fixed_damage = 0

    # Take care of moves that deal damage equal to a percent of the defender hp
    if move.id in ["superfang", "naturesmadness"] and defender.damage_multiplier(move_type) > 0:
        fixed_damage = int(defender.current_hp / 2)

    if move.id == "guardianofalola" and defender.damage_multiplier(move_type) > 0:
        fixed_damage = int(defender.current_hp * 0.75)

    # Some moves work only when the attacker is switched in
    if move.id in ["fakeout", "firstimpression"] and not attacker.first_turn:
        fixed_damage = 0

    if fixed_damage is not None:
        return True, fixed_damage
    else:
        return False, 0


def compute_other_damage_modifiers(move: Move,
                                   move_type: PokemonType,
                                   attacker: Pokemon,
                                   defender: Pokemon,
                                   weather: Weather,
                                   defender_conditions: list[SideCondition]) -> float:
    """
    Computes the damage modifier considering various battle parameters.
    :param move: move under consideration
    :param move_type: move type
    :param attacker: attacking pokémon
    :param defender: defending pokémon
    :param weather: current battle weather
    :param defender_conditions: conditions on the opponent's side
    :return: Damage modifier that takes into account every battle parameter
    """
    damage_modifier = 1

    # Pokémon with the "water absorb", "dry skin" or "storm drain" abilities suffer no damage from water type moves
    if move_type is PokemonType.WATER and ("waterabsorb" in defender.possible_abilities
                                           or "dryskin" in defender.possible_abilities
                                           or "stormdrain" in defender.possible_abilities):
        return 0

    # Pokémon with the "water absorb" ability suffer no damage from water type moves
    if move_type is PokemonType.GROUND and defender.item != "ironball" and \
            ("levitate" in defender.possible_abilities or Effect.MAGNET_RISE in defender.effects):
        return 0

    # If the defender has the "air baloon" item then it takes no damage from ground-type moves
    if move_type is PokemonType.GROUND and defender.item == "airballoon":
        return 0

    # Pokémon with the "volt absorb", "motordrive" or "lightningrod" abilities suffer no damage from electric type moves
    if move_type is PokemonType.ELECTRIC and ("voltabsorb" in defender.possible_abilities
                                              or "motordrive" in defender.possible_abilities
                                              or "lightningrod" in defender.possible_abilities):
        return 0

    # Pokémon with the "flash fire" ability suffer no damage from fire type moves
    if move_type is PokemonType.FIRE and "flashfire" in defender.possible_abilities:
        return 0

    # Pokémon with the "sap sipper" ability suffer no damage from grass type moves
    if move_type is PokemonType.GRASS and "sapsipperr" in defender.possible_abilities:
        return 0

    # Pokémon with the "wonder guard" ability can only take damage from super-effective moves
    if defender.ability == "wonderguard" and defender.damage_multiplier(move_type) < 2:
        return 0

    # Pokémon with the "soundproof" ability suffer no damage from sound-based moves
    if "sound" in move.flags and "soundproof" in defender.possible_abilities:
        return 0

    # The "poltergeist" move deals no damage if the defender has no item
    if move.id == "poltergeist" and defender.item is None:
        return 0

    # Pokémon with the "bulletproof" ability suffer no damage from bullet-based moves
    if defender.ability == "bulletproof" and "bullet" in move.flags:
        return 0

    # Pokémon with the "punk rock" ability suffer no damage from sound-based moves
    if defender.ability == "punkrock" and "sound" in move.flags:
        damage_modifier *= 0.5

    # Pokémon with the following abilities receive 0.75 less damage from super-effective moves
    if defender.ability in ["filter", "solidrock", "prismarmor"] and defender.damage_multiplier(move_type) >= 2:
        damage_modifier *= .75

    # Pokémon with the following abilities receive 0.5 less damage from super-effective moves while at full hp
    if defender.ability in ["multiscale", "shadowshield"] and defender.current_hp_fraction == 1:
        damage_modifier *= 0.5

    # The "heatproof" ability, while defending, reduces fire moves damage,
    # meanwhile the "dry skin" ability does the opposite
    if move_type is PokemonType.FIRE and attacker.ability not in IGNORE_EFFECT_ABILITIES_IDS:
        if defender.ability == "heatproof":
            damage_modifier *= 0.5
        elif defender.ability == "dryskin":
            if weather in [Weather.SUNNYDAY, Weather.DESOLATELAND]:
                damage_modifier *= 2
            else:
                damage_modifier *= 1.25

    # Pokémon with the "rivalry" ability deal 1.25 more damage to pokémon of the same gender,
    # while dealing 0.75 less damage to the ones from the opposite gender
    if attacker.ability == "rivalry" and PokemonGender.NEUTRAL not in [attacker.gender, defender.gender]:
        if attacker.gender == defender.gender:
            damage_modifier *= 1.25
        else:
            damage_modifier *= 0.75

    # Pokémon with the "neuroforce" ability deal 1.25 more damage if they are using a super-effective move
    if attacker.ability == "neuroforce" and defender.damage_multiplier(move_type) >= 2:
        damage_modifier *= 1.25

    # Pokémon with the "water bubble" ability suffer half the damage from fire-type moves
    if defender.ability == "waterbubble" and move_type is PokemonType.FIRE:
        damage_modifier *= 0.5

    # Pokémon with the "ice scales" ability suffer half the damage from special moves
    if defender.ability == "icescales" and move.category is MoveCategory.SPECIAL:
        damage_modifier *= 0.5

    # Pokémon with the "fluffy" ability suffer double the damage from fire-type moves,
    # but suffer half the damage from contact moves
    if defender.ability == "fluffy":
        if move_type is PokemonType.FIRE:
            damage_modifier *= 2
        elif "contact" in move.flags:
            damage_modifier *= 0.5

    # Pokémon with the "merciless" ability deal 1.5 more damage to poisoned pokémon
    if attacker.ability == "merciless" and defender.status in [Status.PSN, Status.TOX] \
            and defender.ability not in ["battlearmor", "shellarmour"]:
        damage_modifier *= 1.5

    # Pokémon with the "flashfire" effect deal 1.5 more damage when using a fire-type move
    if Effect.FLASH_FIRE in attacker.effects and move_type is PokemonType.FIRE:
        damage_modifier *= 1.5

    # Pokémon with the "charge" effect deal double the damage when using an electric-type move
    if Effect.CHARGE in attacker.effects and move_type is PokemonType.ELECTRIC:
        damage_modifier *= 2

    # The "knock-off" move deal 1.5 more damage if the defender is holding an item
    if move.id == "knockoff" and defender.item:
        damage_modifier *= 1.5

    # Some moves do double the damage against dynamaxed pokémon
    if move.id in ["behemothblade", "behemothbash", "dynamaxcannon"] and defender.is_dynamaxed:
        damage_modifier *= 2

    # Some side conditions on the opponent's side halve the move's damage
    if SideCondition.REFLECT in defender_conditions and move.category is MoveCategory.PHYSICAL:
        damage_modifier *= 0.5

    if SideCondition.AURORA_VEIL in defender.effects and move.category is not MoveCategory.Status:
        damage_modifier *= 0.5

    if SideCondition.LIGHT_SCREEN in defender_conditions and move.category is MoveCategory.SPECIAL:
        damage_modifier *= 0.5

    # Pokémon that held the life orb item deal 1.1 damage
    if attacker.item == "lifeorb":
        damage_modifier *= 1.3

    return damage_modifier


def compute_damage(move: Move,
                   attacker: Pokemon,
                   defender: Pokemon,
                   weather: Weather = None,
                   terrains: list[Field] = None,
                   defender_conditions: list[SideCondition] = None,
                   attacker_boosts: dict[str, int] = None,
                   defender_boosts: dict[str, int] = None,
                   is_bot: bool = False,
                   verbose: bool = False) -> dict[str, Union[int | PokemonType]]:
    """
    Computes the damage dealt by a move.
    :param move: move under consideration
    :param attacker: attacking pokémon
    :param defender: defending pokémon
    :param weather: current battle weather
    :param terrains: current terrains on the battle
    :param defender_conditions: conditions on the opponent's side
    :param attacker_boosts: attacker's stat boosts
    :param defender_boosts: defender's stat boosts
    :param is_bot: whether the bot is the attacking pokémon
    :param verbose: print infos aobut the damage computation
    :return: Base power, lower and upper bound of the damage and the new move type
    """
    # Change the move type if some abilities have such effect
    _, move_type = move_changes_type(move, attacker)

    # Deal with fixed damage moves
    is_damage_fixed, fixed_damage = move_fixed_damage(move, move_type, attacker, defender)
    if is_damage_fixed:
        return {"power": move.base_power, "lb": fixed_damage, "ub": fixed_damage, "move_type": move_type}

    # Compute the effect of the attacker level
    level_multiplier = 2 * attacker.level / 5 + 2

    # Compute the move's power
    power: int = compute_base_power(move, move_type, attacker, defender)

    # Compute the ratio between the attacker atk/spa stat and the defender def/spd stat
    if move.category is MoveCategory.PHYSICAL:
        if move.id != "bodypress":
            att_stat = "atk"
        else:
            att_stat = "def"

        def_stat = "def"
    else:
        if move.id not in ["psyshock", "psystrike", "secretsword"]:
            def_stat = "spd"
        else:
            def_stat = "def"

        att_stat = "spa"

    attacker_stat_boost = None
    defender_stat_boost = None

    # Pokémon with the "unaware" ability don't care about stats boosts for the opponent
    if defender.ability == "unaware":
        attacker_stat_boost = 0
    elif attacker_boosts is not None:
        attacker_stat_boost = attacker_boosts[att_stat]

    if attacker.ability == "unaware":
        defender_stat_boost = 0
    elif defender_boosts is not None:
        defender_stat_boost = defender_boosts[def_stat]

    # There are some moves the use the defender's attack to deal damage
    if move.use_target_offensive:
        attacker_stat_value = compute_stat(defender, att_stat, weather, terrains, not is_bot, boost=defender_stat_boost)
    else:
        attacker_stat_value = compute_stat(attacker, att_stat, weather, terrains, is_bot, boost=attacker_stat_boost)

    if att_stat in ["atk", "spa"] and defender.ability == "thickfat" \
            and move_type in [PokemonType.FIRE, PokemonType.ICE]:
        attacker_stat_value *= 0.5

    defender_stat_value = compute_stat(defender, def_stat, weather, terrains, not is_bot, boost=defender_stat_boost)
    ratio_attack_defense = attacker_stat_value / defender_stat_value

    # Compute the base damage before taking into account any modifier
    damage = level_multiplier * power * ratio_attack_defense / 50 + 2

    # Compute the effect of the weather
    weather_multiplier = 1
    if weather and not ("airlock" in [attacker.ability, defender.ability]
                        or "cloudnine" in [attacker.ability, defender.ability]):
        if weather in [Weather.SUNNYDAY, Weather.DESOLATELAND]:
            if move_type is PokemonType.FIRE:
                weather_multiplier = 1.5
            elif move_type is PokemonType.WATER:
                weather_multiplier = 0.5
                if weather is Weather.DESOLATELAND:
                    return {"power": power, "lb": 0, "ub": 0, "move_type": move_type}
        elif weather in [Weather.RAINDANCE, Weather.PRIMORDIALSEA]:
            if move_type is PokemonType.WATER:
                weather_multiplier = 1.5
            elif move_type is PokemonType.FIRE:
                weather_multiplier = 0.5
                if weather is Weather.PRIMORDIALSEA:
                    return {"power": power, "lb": 0, "ub": 0, "move_type": move_type}

    damage *= weather_multiplier

    # Compute the effect of the terrain
    terrain_multiplier = 1
    if terrains:
        if Field.ELECTRIC_TERRAIN in terrains:
            if move_type is PokemonType.ELECTRIC:
                terrain_multiplier = 1.3
        elif Field.GRASSY_TERRAIN in terrains:
            if move_type is PokemonType.GRASS:
                terrain_multiplier = 1.3
            elif move.id in ["earthquake", "magnitude", "bulldoze"]:
                terrain_multiplier = 0.5
        elif Field.MISTY_TERRAIN in terrains:
            if move_type is PokemonType.DRAGON:
                terrain_multiplier = 0.5
        elif Field.PSYCHIC_TERRAIN in terrains:
            if move_type is PokemonType.PSYCHIC:
                terrain_multiplier = 1.3
            elif move.priority > 0:
                return {"power": power, "lb": 0, "ub": 0, "move_type": move_type}

    damage *= terrain_multiplier

    # Compute the effect of the STAB
    if move_type in attacker.types or attacker.ability in ["protean", "libero"]:
        if attacker.ability == "adaptability":
            stab_multiplier = 2
        else:
            stab_multiplier = 1.5
    else:
        stab_multiplier = 1

    damage *= stab_multiplier

    # Compute the effect of the burn
    if attacker.status is Status.BRN and move.category is MoveCategory.PHYSICAL and attacker.ability != "guts" \
            and move.id != "facade":
        damage *= 0.5

    # Compute the effect of the defender's types
    type_multiplier = defender.damage_multiplier(move_type)

    # The move "freeze-dry" is super-effective against water-type pokémon
    if move.id == "freezedry" and PokemonType.ICE in defender.types:
        type_multiplier *= 2

    # The move "thousand-arrows" can deal damage to flying-type pokémon
    if move.id == "thousandarrows" and PokemonType.FLYING in defender.types:
        first_type, second_type = defender.types
        if not second_type:
            type_multiplier = 1
        elif first_type is PokemonType.FLYING:
            type_multiplier = second_type.damage_multiplier(move.type)
        else:
            type_multiplier = first_type.damage_multiplier(move.type)

    damage *= type_multiplier

    # Compute the effect of various abilities and items
    other_damage_modifiers = compute_other_damage_modifiers(move, move_type, attacker, defender,
                                                            weather, defender_conditions)
    damage = int(damage * other_damage_modifiers)

    # Some moves have a perfect critical hit rate
    if move.crit_ratio == 6 and defender.ability not in ["battlearmor", "shellarmour"]:
        damage *= 1.5

    # Define lower and upper bound for the damage after considering moves that hit more than once
    ub_damage = damage * int(move.expected_hits)
    lb_damage = int(ub_damage * 0.85)

    if verbose:
        print("Move under evaluation: {0}".format(move.id))
        print("Base power: {0}, Power: {1}, Type: {2}, Category: {3}".format(move.base_power, power,
                                                                             move_type, move.category.name))
        print("Attacker: {0}, {1}: {2}".format(attacker.species, att_stat, attacker_stat_value))
        print("Defender: {0}, {1}: {2}".format(defender.species, def_stat, defender_stat_value))
        print("Damage: {0} - {1}\n".format(lb_damage, ub_damage))

    return {"power": power, "lb": lb_damage, "ub": ub_damage, "move_type": move_type}
