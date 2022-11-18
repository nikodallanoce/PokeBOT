from poke_env.environment import Pokemon, Battle, Move, MoveCategory, Weather, Field, Status, SideCondition, \
    AbstractBattle
from poke_env.environment.pokemon_type import PokemonType as pt
from poke_env.environment.move import Gen8Move
from src.utilities.stats_utilities import estimate_stat, compute_stat_modifiers, compute_stat_boost


class NodePokemon:
    default_moves = {pt.ROCK: Gen8Move('powergem'),
                     pt.BUG: Gen8Move('xscissor'),
                     pt.DARK: Gen8Move('nightslash'),
                     pt.DRAGON: Gen8Move('dragonpulse'),
                     pt.ELECTRIC: Gen8Move('thunderbolt'),
                     pt.FAIRY: Gen8Move('moonblast'),
                     pt.FIGHTING: Gen8Move('bodypress'),
                     pt.FIRE: Gen8Move('flamethrower'),
                     pt.FLYING: Gen8Move('drillpeck'),
                     pt.GHOST: Gen8Move('moongeistbeam'),
                     pt.GRASS: Gen8Move('energyball'),
                     pt.GROUND: Gen8Move('earthquake'),
                     pt.ICE: Gen8Move('icebeam'),
                     pt.NORMAL: Gen8Move('bodyslam'),
                     pt.POISON: Gen8Move('shellsidearm'),
                     pt.PSYCHIC: Gen8Move('psychic'),
                     pt.STEEL: Gen8Move('flashcannon'),
                     pt.WATER: Gen8Move('surf')
                     }

    def __init__(self, pokemon: Pokemon, is_act_poke: bool, current_hp: int = None,
                 boosts: dict[str, float] = None,
                 status: Status = None, moves: list[Move] = None, effects: dict = None):
        self.pokemon: Pokemon = pokemon
        self.is_act_poke: bool = is_act_poke

        if current_hp is None:
            current_hp = pokemon.current_hp
        elif current_hp < 0:
            current_hp = 0
        self.current_hp: int = current_hp
        assert self.current_hp >= 0

        if boosts is None:
            boosts = pokemon.boosts
        self.boosts: dict[str, float] = boosts

        if status is None:
            status = pokemon.status
        self.status: Status = status

        if len(moves) == 4 or is_act_poke:
            self.moves: list[Move] = list(moves)
        elif not is_act_poke:
            self.moves: list[Move] = self.enrich_moves(list(moves))
        assert self.moves is not None

        if effects is None:
            effects = pokemon.effects
        self.effects: dict = effects

    def is_fainted(self):
        return self.current_hp == 0

    def clone_all(self):
        return NodePokemon(self.pokemon, self.is_act_poke, self.current_hp, self.boosts.copy(), self.status,
                           self.moves.copy(), self.effects.copy())

    def clone(self, is_act_poke: bool = None, current_hp: int = None, boosts: dict[str, float] = None,
              status: Status = None,
              moves: list[Move] = None,
              effects: dict = None):
        if is_act_poke is None:
            is_act_poke = self.is_act_poke
        if current_hp is None:
            current_hp = self.current_hp
        if boosts is None:
            boosts = self.boosts.copy()
        if status is None:
            status = self.status
        if moves is None:
            moves = self.moves.copy()
        if effects is None:
            effects = self.effects.copy()
        return NodePokemon(self.pokemon, is_act_poke, current_hp, boosts, status, moves, effects)

    def retrieve_stats(self, weather: Weather, terrains: list[Field]):

        computed_stats: dict[str, int] = self.pokemon.stats.copy()
        if not self.is_act_poke:
            computed_stats = self.pokemon.base_stats.copy()
            for stat in computed_stats.keys():
                computed_stats[stat] = estimate_stat(self.pokemon, stat)

        for stat in computed_stats.keys():
            computed_stats[stat] = int(
                computed_stats[stat] * compute_stat_modifiers(self.pokemon, stat, weather, terrains))
            computed_stats[stat] = int(computed_stats[stat] * compute_stat_boost(self.pokemon, stat, self.boosts[stat]))

    def enrich_moves(self, known_moves: list[Move]) -> list[Move]:
        moves_added: list[Move] = []
        for poke_type in iter(self.pokemon.types):
            if poke_type is not None:
                move_same_poke_type = False
                for move in known_moves:
                    if move.type == poke_type:
                        move_same_poke_type = True
                        break
                if not move_same_poke_type:
                    def_move: Gen8Move = self.default_moves[poke_type]
                    moves_added.append(def_move)
        return moves_added + known_moves
