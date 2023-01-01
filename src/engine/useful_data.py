from poke_env.environment import SideCondition, Gen8Move, Status
from poke_env.environment.move_category import MoveCategory
from poke_env.environment.pokemon_type import PokemonType

STATUS_CONDITIONS = [Status.BRN, Status.FRZ, Status.PAR, Status.PSN, Status.SLP, Status.TOX]
IGNORE_EFFECT_ABILITIES_IDS = ["moldbreaker", "teravolt", "turboblaze", "neutralizinggas"]
HEALING_MOVES = ["healorder", "milkdrink", "moonlight", "morningsun", "purify", "recover", "rest", "roost", "shoreup",
                 "slackoff", "softboiled", "strengthsap", "synthesis"]
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
