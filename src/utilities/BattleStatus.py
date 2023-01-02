import math
from typing import List

from poke_env.environment import SideCondition
from src.utilities.Heuristic import Heuristic
from src.utilities.NodePokemon import NodePokemon
from src.engine.damage import compute_damage
from src.engine.useful_data import HEALING_MOVES
from src.engine.battle_utilities import *
from src.engine.stats import *


class BattleStatus:
    last_id: int = 0

    def __init__(self, act_poke: NodePokemon, opp_poke: NodePokemon,
                 avail_switches: list[Pokemon],
                 opp_team: list[Pokemon],
                 weather: dict[Weather, int], terrains: list[Field], opp_conditions: list[SideCondition], ancestor,
                 move: Move | Pokemon, poke_switched: bool):
        self.act_poke: NodePokemon = act_poke
        self.opp_poke: NodePokemon = opp_poke
        self.avail_switches: list[Pokemon] = avail_switches
        self.opp_team: list[Pokemon] = opp_team
        self.weather = weather
        self.terrains = terrains
        self.opp_conditions = opp_conditions
        self.ancestor: BattleStatus = ancestor
        self.score = 0
        self.move: Move | Pokemon = move
        self.poke_switched: bool = poke_switched
        self.move_first = self.can_outspeed(0.8)
        self.id = self.last_id
        self.inc_id()

    @classmethod
    def inc_id(cls):
        cls.last_id += 1

    def act_poke_avail_actions(self) -> List[Move | Pokemon]:
        '''
        Computes all the actions that our player can do.
        :return: a list containing all the available actions.
        '''
        # outspeed_p = outspeed_prob(self.act_poke.pokemon, self.opp_poke.pokemon)["outspeed_p"]

        all_actions: list[Move | Pokemon] = []  # self.avail_switches
        if not self.act_poke.is_fainted() and len(self.act_poke.moves) > 0:
            all_actions = self.act_poke.moves + all_actions
        return all_actions

    def opp_poke_avail_actions(self) -> list[Move | Pokemon]:
        '''
        Computes all the actions that the opponent player can do.
        :return: a list containing all the available actions.
        '''
        # all_moves = list[Move | Pokemon]
        all_actions: list[Move | Pokemon] = []  # self.opp_team
        if not self.opp_poke.is_fainted():
            all_actions = self.opp_poke.moves + all_actions
        return all_actions

    def compute_score(self, heuristic: Heuristic, depth: int):
        '''
        Computes the score of a minimax node, given a heuristic.
        :param heuristic: a heuristic that evaluates a node.
        :param depth: current depth of the minimax tree.
        :return: a score of the node.
        '''
        score = heuristic.compute(self, depth)
        return score

    def simulate_action(self, move: Move | Pokemon, is_my_turn: bool):
        '''
        Simulates a next state derived from the current one.
        :param move: a move to apply that will produce a new state.
        :param is_my_turn: true if is our turn, false otherwise.
        :return: a new battle state.
        '''
        weather = None if len(self.weather.keys()) == 0 else next(iter(self.weather.keys()))
        if is_my_turn:
            if isinstance(move, Move):
                damage = self.guess_damage(is_my_turn, move, weather)

                self.weather = self.get_active_weather(move, update_turn=False)
                opp_poke_updated_hp = self.opp_poke.current_hp - damage

                att_boost, def_boost = self.compute_updated_boosts(self.act_poke, self.opp_poke, move)
                act_poke_upd_hp = self.act_poke.current_hp

                heal, _ = self.compute_healing(self.act_poke, move, weather, self.terrains)
                act_poke_upd_hp += heal

                recoil: int = self.compute_recoil(self.act_poke, move, damage)
                act_poke_upd_hp = act_poke_upd_hp - recoil

                # Compute drain dealt by the move
                drain, _ = self.compute_drain(self.act_poke, move, damage)
                act_poke_upd_hp += drain

                opp_poke = self.opp_poke.clone(current_hp=opp_poke_updated_hp, boosts=def_boost)
                act_poke = self.act_poke.clone(current_hp=act_poke_upd_hp, boosts=att_boost)
                opp_team = self.remove_poke_from_switches(opp_poke, self.opp_team)
                child = BattleStatus(act_poke, opp_poke,
                                     self.avail_switches, opp_team, self.weather, self.terrains,
                                     self.opp_conditions, self, move, False)
            else:
                child = BattleStatus(NodePokemon(move, True, moves=list(move.moves.values())), self.opp_poke,
                                     self.avail_switches, self.opp_team, self.weather, self.terrains,
                                     self.opp_conditions, self, move, True)
            return child

        else:

            if isinstance(move, Move):
                damage = compute_damage(move, self.opp_poke.pokemon, self.act_poke.pokemon, weather, self.terrains,
                                        self.opp_conditions, self.opp_poke.boosts, self.act_poke.boosts, is_my_turn)[
                    "ub"]

                att_boost, def_boost = self.compute_updated_boosts(self.opp_poke, self.act_poke, move)
                opp_poke_updated_hp = self.act_poke.current_hp - damage

                act_poke_upd_hp = self.opp_poke.current_hp
                heal, _ = self.compute_healing(self.opp_poke, move, weather, self.terrains)
                act_poke_upd_hp += heal
                recoil: int = self.compute_recoil(self.opp_poke, move, damage)
                act_poke_upd_hp -= recoil
                drain, _ = self.compute_drain(self.act_poke, move, damage)
                act_poke_upd_hp += drain

                act_poke = self.act_poke.clone(current_hp=opp_poke_updated_hp, boosts=def_boost)
                opp_poke = self.opp_poke.clone(current_hp=act_poke_upd_hp, boosts=att_boost)
                avail_switches = self.remove_poke_from_switches(act_poke, self.avail_switches)
                self.weather = self.get_active_weather(move, update_turn=True)

                return BattleStatus(act_poke, opp_poke,
                                    avail_switches, self.opp_team, self.weather, self.terrains,
                                    self.opp_conditions, self, move, False)
            else:
                child = BattleStatus(self.act_poke, NodePokemon(move, False, moves=list(move.moves.values())),
                                     self.avail_switches, self.opp_team, self.weather, self.terrains,
                                     self.opp_conditions, self, move, True)
                return child

    def can_outspeed(self, threshold: float) -> bool:
        '''
        Checks if our Pokemon is probably faster than the opponent's one.
        :param threshold: level of confidence.
        :return: true if our Pokemon is faster, false otherwise.
        '''
        weather = None if len(self.weather.keys()) == 0 else next(iter(self.weather.keys()))
        outspeed_p = outspeed_prob(self.act_poke.pokemon, self.opp_poke.pokemon, weather, self.terrains)[
            "outspeed_p"]
        return outspeed_p < threshold

    def remove_poke_from_switches(self, poke: NodePokemon, team: list[Pokemon]):
        new_team: list[Pokemon] = team
        if poke.is_fainted() and not poke.pokemon.active:
            new_team = team.copy()
            new_team.remove(poke.pokemon)

        return new_team

    def guess_damage(self, is_my_turn, move, weather):
        '''
        Estimates the points of damage that a move could inflict to a Pokemon.
        :param is_my_turn: indicates if is our turn or not.
        :param move: a Pokemon move.
        :param weather: the current weather condition in a battle.
        :return:
        '''
        damage = compute_damage(move, self.act_poke.pokemon, self.opp_poke.pokemon, weather, self.terrains,
                                self.opp_conditions, self.act_poke.boosts, self.opp_poke.boosts, is_my_turn)["lb"]
        # if (move.accuracy is not True) and random.random() > move.accuracy:
        #    damage = 0
        return damage

    def get_active_weather(self, move: Move, update_turn: bool):
        act_weather: dict[Weather, int] = self.weather
        if len(act_weather) > 0 and update_turn:
            act_weather = self.weather.copy()
            for key, val in act_weather.items():
                if val < 5:
                    act_weather[key] = val + 1
                else:
                    act_weather = {}
        if move.weather is not None:
            act_weather = {move.weather: 1}
        return act_weather

    @staticmethod
    def clone_poke_list(poke_list: list[NodePokemon]):
        '''
        Creates a new list that contains all the Pokemon cloned.
        :param poke_list: a list of Pokemon.
        :return: the clone list.
        '''
        cloned_list: list[NodePokemon] = []
        for elem in poke_list:
            cloned_list.append(elem.clone_all())
        return cloned_list

    @staticmethod
    def compute_recoil(poke: NodePokemon, move: Move, damage: int) -> int:
        '''
        Computes the recoil that a move could return.
        :param poke: a node representing the attributes of a Pokemon.
        :param move: a Pokemon move.
        :param damage: the damage that the move inflicts to a Pokemon.
        :return:
        '''
        if move.recoil == 0 or poke.pokemon.ability == "magicguard":
            return 0

        if move.id in ["mindblown", "steelbeam"]:
            recoil = int(poke.pokemon.max_hp / 2)
        elif move.self_destruct:
            recoil = 1000
        else:
            recoil = math.ceil(damage * move.recoil)

        return recoil

    @staticmethod
    def compute_drain(pokemon: NodePokemon, move: Move, damage: int) -> (int, float):
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

        max_hp = pokemon.pokemon.max_hp
        current_hp = pokemon.current_hp

        drain = int(damage * move.drain)
        drain = drain if current_hp + drain <= max_hp else max_hp - current_hp
        drain_percentage = round(drain / max_hp, 2)
        return drain, drain_percentage

    @staticmethod
    def compute_healing(poke: NodePokemon,
                        move: Move,
                        weather: Weather = None,
                        terrains: list[Field] = None) -> (int, float):
        '''
        Computes the healing health points that a move could return.
        :param poke: a node representing the attributes of a Pokemon.
        :param move: move under consideration.
        :param weather: the current weather condition in a battle.
        :param terrains: the current active field in a battle.
        :return: a tuple representing the healing points and the corresponding percentage.
        '''
        healing = 0
        healing_percentage = 0.0
        if move.category is MoveCategory.STATUS and move.heal > 0:
            healing = None
            healing_percentage = 0.5
            if poke.pokemon.is_dynamaxed or move.id not in HEALING_MOVES:
                return 0, 0

            max_hp = poke.pokemon.max_hp
            current_hp = poke.current_hp

            if move.id in ["morningsun", "moonlight", "synthesis"]:
                if weather in [Weather.SUNNYDAY, Weather.DESOLATELAND]:
                    healing_percentage = 0.66
                elif weather in [Weather.RAINDANCE, Weather.PRIMORDIALSEA, Weather.HAIL, Weather.SANDSTORM]:
                    healing_percentage = 0.25

            # We assume that bot doesn't heal the opponent's pokémon from its status conditions
            if move.id == "purify" and poke.status not in STATUS_CONDITIONS:
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
                atk_boost = poke.boosts["atk"]
                if poke.pokemon.ability == "contrary":
                    atk_boost = atk_boost + 1 if atk_boost < 6 else 6
                elif atk_boost == -6:
                    return 0, 0
                else:
                    atk_boost = atk_boost - 1 if atk_boost > -6 else -6

                if poke.is_act_poke:
                    atk_stat = poke.pokemon.stats["atk"]
                else:
                    atk_stat = estimate_stat(poke.pokemon, "atk")

                atk_stat *= compute_stat_modifiers(poke.pokemon, "atk", weather, terrains)
                healing = int(atk_stat * compute_stat_boost(poke.pokemon, "atk", atk_boost))

            if healing is None:
                healing = int(max_hp * healing_percentage)

            healing = healing if current_hp + healing <= max_hp else max_hp - current_hp
            healing_percentage = round(healing / max_hp, 2)
        return healing, healing_percentage

    @staticmethod
    def compute_updated_boosts(att_poke: NodePokemon, def_poke: NodePokemon, move: Move):
        '''
        Updates the attacker and the defender statistic boost.
        :param att_poke: a node representing the attributes of the defender Pokemon.
        :param def_poke: a node representing the attributes of the attacker Pokemon.
        :param move: a Pokemon move.
        :return: the updated boosts
        '''
        att_upd_boosts = att_poke.boosts.copy()
        def_upd_boosts = def_poke.boosts.copy()
        boosts = move.self_boost if move.boosts is None else move.boosts
        if boosts is not None:
            if move.target == 'self':
                for stat_boost, boost in boosts.items():
                    # upd_stats = compute_stat_boost(att_poke.pokemon, stat_boost, boost)
                    att_upd_boosts[stat_boost] += boost
            elif move.target == 'normal':
                for stat_boost, boost in boosts.items():
                    def_upd_boosts[stat_boost] += boost

        return att_upd_boosts, def_upd_boosts

    def __str__(self):
        mv = self.move.species if isinstance(self.move, Pokemon) else str(self.move).split(" ")[0]
        to_string = "My: " + self.act_poke.pokemon.species + "  opp: " + self.opp_poke.pokemon.species
        to_string = to_string + "  sc: " + str(round(self.score, 2)) + "  mv: " + mv + "  mf: " + str(
            self.move_first) + " an: " + str(self.ancestor.id)
        return to_string
