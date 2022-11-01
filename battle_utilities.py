from poke_env.environment import Pokemon, Move, Weather, Field, Status
from poke_env.environment.move_category import MoveCategory
from poke_env.data import NATURES
from poke_env.environment.pokemon_type import PokemonType
from poke_env.environment.pokemon_gender import PokemonGender


STATUS_CONDITIONS = [Status.BRN, Status.FRZ, Status.PAR, Status.PSN, Status.SLP, Status.TOX]
PUNCHING_MOVES_IDS = ["bulletpunch", "cometpunch", "dizzypunch", "doubleironbash", "drainpunch", "dynamicpunch",
                      "firepunch", "focuspunch", "hammerarm", "icehammer", "icepunch", "machpunch",
                      "megapunch", "poweruppunch", "shadowpunch", "skyuppercut", "thunderpunch"]
BITING_MOVES_IDS = ["bite", "crunch", "firefang", "fishiousrend", "hyperfang", "icefang", "jawlock", "poisonfang",
                    "psychicfang", "thunderfang"]
SOUND_BASED_MOVES_IDS = ["boomburst", "bugbuzz", "chatter", "clangingscales", "clangoroussoul", "clangoroussoulblaze",
                         "disarmingvoice", "echoedvoice", "eeriespell", "grasswhistle", "growl", "healbell", "howl",
                         "hypervoice", "metalsound", "nobleroar", "overdrive", "partingshot", "perishsong", "relicsong",
                         "roar", "round", "screech", "shadowpanic", "sing", "snarl", "snore",
                         "sparklingaura", "supersonic", "uproar"]
AURA_PULSE_MOVES_IDS = ["aurasphere", "darkpulse", "dragonpulse", "healpulse", "originpulse",
                        "terrainpulse", "waterpulse"]
IGNORE_EFFECT_ABILITIES_IDS = ["moldbreaker", "teravolt", "turboblaze"]


def estimate_stat(pokemon: Pokemon, stat: str, ivs: int = 31, evs: int = 21, nature: str = "Neutral") -> int:
    estimated_stat = 2 * pokemon.base_stats[stat] + ivs + evs
    estimated_stat = int(estimated_stat * pokemon.level / 100) + 5

    # The hp stat has a different computation than the others
    if stat == "hp":
        if pokemon.species == "shedinja":
            return 1

        estimated_stat += pokemon.level + 5
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


def __compute_base_power_multipliers(move: Move, attacker: Pokemon, defender: Pokemon) -> [float, PokemonType]:
    move_type = move.type
    base_power_multiplier = 1

    # The power of the move "facade" is double if the user has a status condition
    if move.id == "facade" and attacker.status in STATUS_CONDITIONS:
        base_power_multiplier *= 2

    # The power of the move "brine" is doubled if the user hp is <= 1/2
    if move.id == "brine" and attacker.current_hp_fraction <= 0.5:
        base_power_multiplier *= 2

    # The power of the move "venoshock" is doubled if the defender is poisoned
    if move.id == "venoshock" and defender.status in [Status.PSN, Status.TOX]:
        base_power_multiplier *= 2

    # Pokèmon with the rivalry ability deal 1.25 more damage to pokèmon of the same gender,
    # while dealing 0.75 less damage to the ones from the opposite gender
    if attacker.ability == "rivalry" and attacker.gender is not PokemonGender.NEUTRAL:
        if attacker.gender == defender.gender:
            base_power_multiplier *= 1.25
        else:
            base_power_multiplier *= 0.75

    # Moves of pokèmon with the following abilities have their power increased if the hp is less or equal than 1/3
    if attacker.current_hp_fraction <= 0.33:
        if attacker.ability == "overgrow" and move_type is PokemonType.GRASS:
            base_power_multiplier *= 1.5

        if attacker.ability == "blaze" and move_type is PokemonType.FIRE:
            base_power_multiplier *= 1.5

        if attacker.ability == "torrent" and move_type is PokemonType.WATER:
            base_power_multiplier *= 1.5

        if attacker.ability == "swarm" and move_type is PokemonType.BUG:
            base_power_multiplier *= 1.5

    # The "reckless" ability boosts power of moves with recoil
    if attacker.ability == "reckless" and move.recoil > 0:
        base_power_multiplier *= 1.2

    # The "iron fist" ability boosts power of punching moves
    if attacker.ability == "ironfist" and move.id in PUNCHING_MOVES_IDS:
        base_power_multiplier *= 1.2

    # The "normalize" ability changes all move types to normal-type and boosts their power
    if attacker.ability == "normalize" and move_type is not PokemonType.NORMAL:
        move_type = PokemonType.NORMAL
        base_power_multiplier *= 1.2

    # The "aerilate" ability changes all normal-type moves to flying-type and boosts their power
    if attacker.ability == "aerilate" and move_type is PokemonType.NORMAL:
        move_type = PokemonType.FLYING
        base_power_multiplier *= 1.2

    # The "refrigerate" ability changes all normal-type moves to ice-type and boosts their power
    if attacker.ability == "refrigerate" and move_type is PokemonType.NORMAL:
        move_type = PokemonType.ICE
        base_power_multiplier *= 1.2

    # The "pixilate" ability changes all normal-type moves to fairy-type and boosts their power
    if attacker.ability == "pixilate" and move_type is PokemonType.NORMAL:
        move_type = PokemonType.FAIRY
        base_power_multiplier *= 1.2

    # The "galvanize" ability changes all normal-type moves to electric-type and boosts their power
    if attacker.ability == "galvanize" and move_type is PokemonType.NORMAL:
        move_type = PokemonType.ELECTRIC
        base_power_multiplier *= 1.2

    # The "punk rock" ability boosts the power of sound-based moves
    if attacker.ability == "punkrock" and move.id in SOUND_BASED_MOVES_IDS:
        base_power_multiplier *= 1.3

    # If a pokèmon with the "dark aura" ability is active, the power of dark-type moves is increased
    if "darkaura" in [attacker.ability, defender.ability] and move_type is PokemonType.DARK:
        # If a pokèmon with the "aura break" ability is active, the power of dark-type moves is decreased
        if "aurabreak" not in [attacker.ability, defender.ability]:
            base_power_multiplier *= 1.33
        elif attacker.ability not in IGNORE_EFFECT_ABILITIES_IDS:
            base_power_multiplier *= 0.75

    # If a pokèmon with the "fairy aura" ability is active, the power of fairy-type moves is increased
    if "fairyaura" in [attacker.ability, defender.ability] and move_type is PokemonType.FAIRY:
        # If a pokèmon with the "aura break" ability is active, the power of fairy-type moves is decreased
        if "aurabreak" not in [attacker.ability, defender.ability]:
            base_power_multiplier *= 1.33
        elif attacker.ability not in IGNORE_EFFECT_ABILITIES_IDS:
            base_power_multiplier *= 0.75

    # The "strong jaw" ability boosts the power of biting moves
    if attacker.ability == "strongjaw" and move.id in BITING_MOVES_IDS:
        base_power_multiplier *= 1.5

    # The "mega-launcher" ability boosts the power of aura and pulse moves
    if attacker.ability == "megalauncher" and move.id in AURA_PULSE_MOVES_IDS:
        base_power_multiplier *= 1.5

    # The "technician" ability boosts the power of moves with a base power <= 60
    if attacker.ability == "technician" and move.base_power <= 60:
        base_power_multiplier *= 1.5

    # The "toxic boost" ability boosts the power of physical moves if the user is poisoned
    if attacker.ability == "toxicboost" and move.category is MoveCategory.PHYSICAL \
            and attacker.status in [Status.PSN, Status.TOX]:
        base_power_multiplier *= 1.5

    # The "flare boost" ability boosts the power of special moves if the user is burned
    if attacker.ability == "flareboost" and move.category is MoveCategory.SPECIAL and attacker.status in [Status.BRN]:
        base_power_multiplier *= 1.5

    # The "dragon's maw" ability boosts the power of dragon-type moves
    if attacker.ability == "dragonsmaw" and move_type is PokemonType.DRAGON:
        base_power_multiplier *= 1.5

    # The "transistor" ability boosts the power of electric-type moves
    if attacker.ability == "transistor" and move_type is PokemonType.ELECTRIC:
        base_power_multiplier *= 1.5

    # The "steelworker" and "steely spirit" abilities boost the power of steel-type moves
    if attacker.ability in ["steelworker", "steelyspirit"] and move_type is PokemonType.STEEL:
        base_power_multiplier *= 1.5

    # The "heatproof" ability, while defending, reduces the power of fire moves,
    # meanwhile the "dry skin" ability does the opposite
    if move_type is PokemonType.FIRE and attacker.ability not in IGNORE_EFFECT_ABILITIES_IDS:
        if defender.ability == "heatproof":
            base_power_multiplier *= 0.5
        elif defender.ability == "dryskin":
            base_power_multiplier *= 1.25

    # The "muscleband" item boosts the power of physical moves
    if attacker.item == "muscleband" and move.category is MoveCategory.PHYSICAL:
        base_power_multiplier *= 1.1

    # The "wise glasses" item boosts the power of special moves
    if attacker.item == "wiseglasses" and move.category is MoveCategory.SPECIAL:
        base_power_multiplier *= 1.1

    return base_power_multiplier, move_type


def __compute_other_damage_multipliers(move: Move, attacker: Pokemon, defender: Pokemon) -> float:
    damage_multiplier = 1

    move_type = move.type

    # Pokèmon with the water absorb ability suffer no damage from water type moves
    if move_type is PokemonType.WATER and defender.ability == "waterabsorb":
        return 0

    # Pokèmon with the volt absorb ability suffer no damage from electric type moves
    if move_type is PokemonType.ELECTRIC and defender.ability == "voltabsorb":
        return 0

    # Pokèmon with the flash fire ability suffer no damage from fire type moves
    if move_type is PokemonType.FIRE and defender.ability == "flashfire":
        return 0

    # Pokèmon with the sap sipper ability suffer no damage from grass type moves
    if move_type is PokemonType.GRASS and defender.ability == "sapsipperr":
        return 0

    # Pokèmon with the wonder guard ability can only take damage from super-effective moves
    if defender.ability == "wonderguard" and defender.damage_multiplier(move) < 2:
        return 0

    # Pokèmon with the following abilities receive 0.75 less damage from super-effective moves
    if defender.ability in ["filter", "solidrock", "prismarmor"] and defender.damage_multiplier(move) >= 2:
        damage_multiplier *= .75

    # Pokèmon with the following abilities receive 0.5 less damage from super-effective moves while at full hp
    if defender.ability in ["multiscale", "shadowshield"] and defender.current_hp_fraction == 1\
            and defender.damage_multiplier(move) >= 2:
        damage_multiplier *= 0.5

    # Pokèmon with the neuroforce ability deal 1.25 more damage if they are using a super-effective move
    if attacker.ability == "neuroforce" and defender.damage_multiplier(move) >= 2:
        damage_multiplier *= 1.25

    # Pokèmon that held the life orb item deal 1.1 damage
    if attacker.item == "lifeorb":
        damage_multiplier *= 1.299

    return damage_multiplier


def compute_damage(move: Move,
                   attacker: Pokemon,
                   defender: Pokemon,
                   weather_list: list,
                   field_list: list,
                   is_bot: bool,
                   verbose: bool = False) -> int:
    if move.category is MoveCategory.STATUS:
        return 0

    # Take care of moves that do fixed damage or equal to the attacker's level
    if type(move.damage) is not str:
        if move.damage > 0:
            return move.damage
    else:
        return attacker.level

    # One hit KO moves do as much damage as the remaining hp if the attacker's level is equal or higher
    # than the defender's, otherwise they deal no damage
    if move.id in ["fissure", "guillotine", "horndrill", "sheercold"]:
        if defender.level <= attacker.level and defender.damage_multiplier(move) > 0:
            return defender.current_hp
        else:
            return 0

    # Take care of moves that deals damage equals to a percent of the defender hp
    if move.id in ["superfang", "naturesmadness"] and defender.damage_multiplier(move) > 0:
        return int(defender.current_hp / 2)

    if move.id == "guardianofalola" and defender.damage_multiplier(move) > 0:
        return int(defender.current_hp * 0.75)

    # move_type = move.type
    base_power = move.base_power

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
        attack_stat *= compute_stat_boost(attacker, boosts_to_consider[0])

    if attacker.ability != "unaware":
        defense_stat *= compute_stat_boost(defender, boosts_to_consider[1])

    ratio_attack_defense = attack_stat / defense_stat
    if verbose:
        print("Move under evaluation: {0}".format(move.id))
        print("Attacker (Bot): {0}, {1} Attack: {2}".format(attacker.species, move.category.name, int(attack_stat)))
        print("Defender: {0}, {1} Defense: {2}".format(defender.species, move.category.name, int(defense_stat)))

    # Compute the move's power
    base_power_multiplier, move_type = __compute_base_power_multipliers(move, attacker, defender)
    power = int(base_power * base_power_multiplier)
    if verbose:
        print("Base power: {0}, Power: {1}, Type: {2}".format(base_power, power, move_type))

    # Change the move type by effect of the attacker ability and held item
    if attacker.ability == "multitype" and move.id == "judgement" and attacker.item[-5:] == "plate":
        move_type = PokemonType.from_name(attacker.item[:-5])

    if attacker.ability == "rkssystem" and move.id == "multiattack" and attacker.item[-6:] == "memory":
        move_type = PokemonType.from_name(attacker.item[:-6])

    # Compute the base damage before taking into account any modifier
    damage = level_multiplier * power * ratio_attack_defense / 50 + 2

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

    damage *= weather_multiplier

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

    damage *= field_multiplier

    # Compute the effect of the STAB
    if move_type in attacker.types:
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
    type_multiplier = defender.damage_multiplier(move)
    damage *= type_multiplier

    # Compute the effect of various abilities and items
    other_damage_multipliers = __compute_other_damage_multipliers(move, attacker, defender)
    damage = int(damage * other_damage_multipliers)

    # The move false swipe will never kill the pokèmon
    if move.id == "falseswipe" and defender.current_hp <= damage:
        damage = defender.current_hp - 1

    if verbose:
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
        return round(prob_out_speed, 2)
