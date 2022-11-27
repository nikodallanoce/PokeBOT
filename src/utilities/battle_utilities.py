from poke_env.environment import Pokemon, Move, Weather, Field, Status, SideCondition, PokemonGender, Effect,\
    AbstractBattle, Gen8Move
from poke_env.environment.move_category import MoveCategory
from poke_env.environment.pokemon_type import PokemonType
from src.utilities.stats_utilities import estimate_stat, compute_stat_boost, compute_stat_modifiers,\
    compute_stat, stats_to_string, STATUS_CONDITIONS
from src.utilities.utilities import types_to_string
from typing import Union

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
PERFECT_CRIT_RATE_MOVES_IDS = ["frostbreath", "stormthrow", "surgingstrikes", "wickedblow", "zippyzap"]
PROTECTING_MOVES = ["banefulbunker", "detect", "kingsshield", "matblock", "obstruct", "protect",
                    "spikyshield", "wideguard"]
HEALING_MOVES = ["healorder", "milkdrink", "moonlight", "morningsun", "purify", "recover", "rest", "roost", "shoreup",
                 "slackoff", "softboiled", "strengthsap", "synthesis"]
IGNORE_EFFECT_ABILITIES_IDS = ["moldbreaker", "teravolt", "turboblaze", "neutralizinggas"]
ENTRY_HAZARDS = {"spikes": SideCondition.SPIKES, "stealhrock": SideCondition.STEALTH_ROCK,
                 "stickyweb": SideCondition.STICKY_WEB, "toxicspikes": SideCondition.TOXIC_SPIKES}
ANTI_HAZARDS_MOVES = ["rapidspin", "defog"]
DEFAULT_MOVES_IDS = {PokemonType.BUG: {MoveCategory.PHYSICAL: Gen8Move("xscissor"),
                                       MoveCategory.SPECIAL: Gen8Move("bugbuzz")},
                     PokemonType.DARK: {MoveCategory.PHYSICAL: Gen8Move("crunch"),
                                        MoveCategory.SPECIAL: Gen8Move("darkpulse")},
                     PokemonType.DRAGON: {MoveCategory.PHYSICAL: Gen8Move("outrage"),
                                          MoveCategory.SPECIAL: Gen8Move("dragonpulse")},
                     PokemonType.ELECTRIC: {MoveCategory.PHYSICAL: Gen8Move("wildcharge"),
                                            MoveCategory.SPECIAL: Gen8Move("thunderbolt")},
                     PokemonType.FAIRY: {MoveCategory.PHYSICAL: Gen8Move("playrough"),
                                         MoveCategory.SPECIAL: Gen8Move("moonblast")},
                     PokemonType.FIGHTING: {MoveCategory.PHYSICAL: Gen8Move("closecombat"),
                                            MoveCategory.SPECIAL: Gen8Move("focusblast")},
                     PokemonType.FIRE: {MoveCategory.PHYSICAL: Gen8Move("flareblitz"),
                                        MoveCategory.SPECIAL: Gen8Move("fireblast")},
                     PokemonType.FLYING: {MoveCategory.PHYSICAL: Gen8Move("fly"),
                                          MoveCategory.SPECIAL: Gen8Move("hurricane")},
                     PokemonType.GHOST: {MoveCategory.PHYSICAL: Gen8Move("shadowclaw"),
                                         MoveCategory.SPECIAL: Gen8Move("shadowball")},
                     PokemonType.GRASS: {MoveCategory.PHYSICAL: Gen8Move("powerwhip"),
                                         MoveCategory.SPECIAL: Gen8Move("energyball")},
                     PokemonType.GROUND: {MoveCategory.PHYSICAL: Gen8Move("earthquake"),
                                          MoveCategory.SPECIAL: Gen8Move("earthpower")},
                     PokemonType.ICE: {MoveCategory.PHYSICAL: Gen8Move("icefang"),
                                       MoveCategory.SPECIAL: Gen8Move("icebeam")},
                     PokemonType.NORMAL: {MoveCategory.PHYSICAL: Gen8Move("doubleedge"),
                                          MoveCategory.SPECIAL: Gen8Move("hypervoice")},
                     PokemonType.POISON: {MoveCategory.PHYSICAL: Gen8Move("gunkshot"),
                                          MoveCategory.SPECIAL: Gen8Move("sludgebomb")},
                     PokemonType.PSYCHIC: {MoveCategory.PHYSICAL: Gen8Move("zenheadbutt"),
                                           MoveCategory.SPECIAL: Gen8Move("psychic")},
                     PokemonType.ROCK: {MoveCategory.PHYSICAL: Gen8Move("stoneedge"),
                                        MoveCategory.SPECIAL: Gen8Move("powergem")},
                     PokemonType.STEEL: {MoveCategory.PHYSICAL: Gen8Move("ironhead"),
                                         MoveCategory.SPECIAL: Gen8Move("flashcannon")},
                     PokemonType.WATER: {MoveCategory.PHYSICAL: Gen8Move("waterfall"),
                                         MoveCategory.SPECIAL: Gen8Move("surf")}}


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
    if attacker.ability == "liquidvoice" and move.id in SOUND_BASED_MOVES_IDS:
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


def compute_base_power_modifiers(move: Move, move_type: PokemonType, attacker: Pokemon, defender: Pokemon) -> float:
    """
    Computes the modifiers of a move's base power considering the abilities and items of the active pokémon.

    :param move: move under consideration
    :param move_type: move type
    :param attacker: attacking pokémon
    :param defender: defending pokémon
    :return: Base power modifier that takes into account abilities and items
    """
    base_power_modifier = 1

    # The power of the move "facade" is double if the user has a status condition
    if move.id == "facade" and attacker.status in STATUS_CONDITIONS:
        base_power_modifier *= 2

    # The power of the move "brine" is doubled if the user hp is <= 1/2
    if move.id == "brine" and attacker.current_hp_fraction <= 0.5:
        base_power_modifier *= 2

    # The power of the move "venoshock" is doubled if the defender is poisoned
    if move.id == "venoshock" and defender.status in [Status.PSN, Status.TOX]:
        base_power_modifier *= 2

    # Moves of pok*mon with the following abilities have their power increased if the hp is less or equal than 1/3
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
    if attacker.ability == "ironfist" and move.id in PUNCHING_MOVES_IDS:
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

    if attacker.ability == "waterbubble" and move_type is PokemonType.WATER:
        base_power_modifier *= 2

    if move.id == "hex" and defender.status in STATUS_CONDITIONS:
        base_power_modifier *= 2

    # The "punk rock" ability boosts the power of sound-based moves
    if attacker.ability == "punkrock" and move.id in SOUND_BASED_MOVES_IDS:
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
    if attacker.ability == "strongjaw" and move.id in BITING_MOVES_IDS:
        base_power_modifier *= 1.5

    # The "mega-launcher" ability boosts the power of aura and pulse moves
    if attacker.ability == "megalauncher" and move.id in AURA_PULSE_MOVES_IDS:
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

    # The "muscleband" item boosts the power of physical moves
    if attacker.item == "muscleband" and move.category is MoveCategory.PHYSICAL:
        base_power_modifier *= 1.1

    # The "wise glasses" item boosts the power of special moves
    if attacker.item == "wiseglasses" and move.category is MoveCategory.SPECIAL:
        base_power_modifier *= 1.1

    return base_power_modifier


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

    # Pokémon with the water absorb ability suffer no damage from water type moves
    if move_type is PokemonType.WATER and ("waterabsorb" in defender.possible_abilities
                                           or "dryskin" in defender.possible_abilities
                                           or "stormdrain" in defender.possible_abilities):
        return 0

    # Pokémon with the water absorb ability suffer no damage from water type moves
    if move_type is PokemonType.GROUND and defender.item != "ironball" and\
            ("levitate" in defender.possible_abilities or Effect.MAGNET_RISE in defender.effects):
        return 0

    # If the defender has the "air baloon" item then it takes no damage from ground-type moves
    if move_type is PokemonType.GROUND and defender.item == "airballoon":
        return 0

    # Pokémon with the volt absorb ability suffer no damage from electric type moves
    if move_type is PokemonType.ELECTRIC and ("voltabsorb" in defender.possible_abilities
                                              or "motordrive" in defender.possible_abilities
                                              or "lightningrod" in defender.possible_abilities):
        return 0

    # Pokémon with the flash fire ability suffer no damage from fire type moves
    if move_type is PokemonType.FIRE and "flashfire" in defender.possible_abilities:
        return 0

    # Pokémon with the sap sipper ability suffer no damage from grass type moves
    if move_type is PokemonType.GRASS and "sapsipperr" in defender.possible_abilities:
        return 0

    # Pokémon with the wonder guard ability can only take damage from super-effective moves
    if defender.ability == "wonderguard" and defender.damage_multiplier(move_type) < 2:
        return 0

    if move.id in SOUND_BASED_MOVES_IDS and "soundproof" in defender.possible_abilities:
        return 0

    if move.id == "poltergeist" and defender.item is None:
        return 0

    if defender.ability == "punkrock" and move.id in SOUND_BASED_MOVES_IDS:
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

    # Pokémon with the rivalry ability deal 1.25 more damage to pokémon of the same gender,
    # while dealing 0.75 less damage to the ones from the opposite gender
    if attacker.ability == "rivalry" and PokemonGender.NEUTRAL not in [attacker.gender, defender.gender]:
        if attacker.gender == defender.gender:
            damage_modifier *= 1.25
        else:
            damage_modifier *= 0.75

    # Pokémon with the neuroforce ability deal 1.25 more damage if they are using a super-effective move
    if attacker.ability == "neuroforce" and defender.damage_multiplier(move_type) >= 2:
        damage_modifier *= 1.25

    # Pokémon with the "water bubble" ability suffer half the damage from fire-type moves
    if defender.ability == "waterbubble" and move_type is PokemonType.FIRE:
        damage_modifier *= 0.5

    # Pokémon with the "ice scales" ability suffer half the damage from special moves
    if defender.ability == "icescales" and move.category is MoveCategory.SPECIAL:
        damage_modifier *= 0.5

    # Pokémon with the "fluffy" ability suffer double the damage from fire-type moves
    if defender.ability == "fluffy" and move_type is PokemonType.FIRE:
        damage_modifier *= 2

    # Pokémon with the "merciless" ability deal 1.5 more damage to poisoned pokémon
    if attacker.ability == "merciless" and defender.status in [Status.PSN, Status.TOX]\
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

    if SideCondition.LIGHT_SCREEN in defender.effects and move.category is MoveCategory.SPECIAL:
        damage_modifier *= 0.5

    # Pokémon that held the life orb item deal 1.1 damage
    if attacker.item == "lifeorb":
        damage_modifier *= 1.299

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
    power = move.base_power
    if move.id in ["eruption", "waterspout"]:
        attacker_max_hp = compute_stat(attacker, "hp", weather, terrains, is_bot)
        attacker_current_hp = int(attacker_max_hp * attacker.current_hp_fraction)
        power = int(150 * attacker_current_hp / attacker_max_hp)
        if power < 1:
            power = 1

    power = int(power * compute_base_power_modifiers(move, move_type, attacker, defender))

    if verbose:
        print("Base power: {0}, Power: {1}, Type: {2}".format(move.base_power, power, move_type))

    # Compute the ratio between the attacker atk/spa stat and the defender def/spd stat
    attacker_stat = {"stat": None, "value": 0}
    defender_stat = {"stat": None, "value": 0}
    if move.category is MoveCategory.PHYSICAL:
        if move.id != "bodypress":
            attacker_stat["stat"] = "atk"
        else:
            attacker_stat["stat"] = "def"

        defender_stat["stat"] = "def"
    else:
        if move.id not in ["psyshock", "psystrike", "secretsword"]:
            defender_stat["stat"] = "spd"
        else:
            defender_stat["stat"] = "def"

        attacker_stat["stat"] = "spa"

    att_stat = attacker_stat["stat"]
    def_stat = defender_stat["stat"]
    if is_bot:
        attacker_stat["value"] = attacker.stats[att_stat]
        defender_stat["value"] = defender.base_stats[def_stat]
        defender_stat["value"] = estimate_stat(defender, def_stat)
    else:
        attacker_stat["value"] = attacker.base_stats[att_stat]
        attacker_stat["value"] = estimate_stat(attacker, att_stat)
        defender_stat["value"] = defender.stats[def_stat]

    # Compute stat modifiers
    attacker_stat["value"] *= compute_stat_modifiers(attacker, attacker_stat["stat"], weather, terrains)
    if attacker_stat["stat"] in ["atk", "spa"] and defender.ability == "thickfat"\
            and move_type in [PokemonType.FIRE, PokemonType.ICE]:
        attacker_stat["value"] *= 0.5

    defender_stat["value"] *= compute_stat_modifiers(defender, defender_stat["stat"], weather, terrains)

    # Pokémon with the "unaware" ability don't care about stats boosts for the opponent
    if defender.ability != "unaware":
        boost = attacker_boosts[attacker_stat["stat"]] if attacker_boosts else attacker.boosts[attacker_stat["stat"]]
        attacker_stat["value"] *= compute_stat_boost(attacker, attacker_stat["stat"], boost)

    if attacker.ability != "unaware":
        boost = defender_boosts[defender_stat["stat"]] if defender_boosts else defender.boosts[defender_stat["stat"]]
        defender_stat["value"] *= compute_stat_boost(defender, defender_stat["stat"], boost)

    ratio_attack_defense = int(attacker_stat["value"]) / int(defender_stat["value"])
    if verbose:
        print("Move under evaluation: {0}".format(move.id))
        print("Attacker: {0}, {1} {2}: {3}".format(attacker.species, move.category.name,
                                                   attacker_stat["stat"], int(attacker_stat["value"])))
        print("Defender: {0}, {1} {2}: {3}".format(defender.species, move.category.name,
                                                   defender_stat["stat"], int(defender_stat["value"])))

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

    # There are moves that hit more than time
    damage *= int(move.expected_hits)

    if verbose:
        print("Damage: {0}\n".format(damage))

    return {"power": power, "lb": int(damage * 0.85), "ub": damage, "move_type": move_type}


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

    if attacker.ability == "hustle" and move.category is MoveCategory.PHYSICAL:
        accuracy *= 0.8

    # Apply modifiers to attacker's accuracy and defender's evasion
    accuracy *= compute_stat_modifiers(attacker, "accuracy", weather, terrains)
    evasion = compute_stat_modifiers(defender, "evasion", weather, terrains)

    # Compute boosts to the previous stats
    accuracy *= compute_stat_boost(attacker, "accuracy", attacker_accuracy_boost)
    evasion *= compute_stat_boost(defender, "evasion", defender_evasion_boost)

    # Compute move accuracy
    move_accuracy = accuracy / evasion

    if verbose:
        print("Move {0} accuracy: {1}".format(move.id, move_accuracy))

    return round(move_accuracy, 2)


def compute_healing(attacker: Pokemon,
                    defender: Pokemon,
                    move: Move,
                    weather: Weather = None,
                    terrains: list[Field] = None,
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
