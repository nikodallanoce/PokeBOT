from poke_env.environment import Pokemon, Battle, Move, MoveCategory, Weather, Field, Status, SideCondition, \
    AbstractBattle
from poke_env.environment.pokemon_type import PokemonType as pt
from poke_env.environment.move import Gen8Move


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

    def __init__(self, pokemon: Pokemon, current_hp: int = None, current_stats: dict[str, int] = None,
                 status: Status = None, moves: list[Move] = None):
        self.pokemon = pokemon

        if current_hp is None:
            current_hp = pokemon.current_hp
        self.current_hp = current_hp

        if current_stats is None:
            current_stats = pokemon.stats
        self.current_stats = current_stats

        if status is None:
            status = pokemon.status
        self.status = status

        if moves is None:
            if len(pokemon.moves) == 4:
                moves = list(pokemon.moves.values())
            else:
                moves = self.enrich_moves(list(pokemon.moves.values()))

        self.moves = moves

    def clone_all(self):
        return NodePokemon(self.pokemon, self.current_hp, self.current_stats.copy(), self.status, self.moves.copy())

    def clone(self, current_hp: int = None, current_stats: dict[str, int] = None, status: Status = None,
              moves: list[Move] = None):
        if current_hp is None:
            current_hp = self.current_hp
        if current_stats is None:
            current_stats = self.current_stats.copy()
        if status is None:
            status = self.status
        if moves is None:
            moves = self.moves.copy()
        return NodePokemon(self.pokemon, current_hp, current_stats, status, moves)

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
