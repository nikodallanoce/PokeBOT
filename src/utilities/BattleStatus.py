from src.utilities.Heuristic import Heuristic
from src.utilities.NodePokemon import NodePokemon
from src.utilities.battle_utilities import *
from src.utilities.stats_utilities import *
import random


class BattleStatus:

    def __init__(self, act_poke: NodePokemon, opp_poke: NodePokemon,
                 avail_switches: list[Pokemon],
                 weather: dict[Weather, int], terrains: list[Field], opp_conditions: list[SideCondition], ancestor,
                 move: Move | Pokemon):
        self.act_poke = act_poke
        self.opp_poke = opp_poke
        self.avail_switches = avail_switches
        self.weather = weather
        self.terrains = terrains
        self.opp_conditions = opp_conditions
        self.ancestor = ancestor
        self.score = 0
        self.move = move

    def act_poke_avail_actions(self) -> list[Move | Pokemon]:
        all_actions: list[Move | Pokemon] = self.avail_switches
        if not self.act_poke.is_fainted():
            all_actions = self.act_poke.moves + all_actions
        return all_actions

    def opp_poke_avail_actions(self):
        all_moves = []
        if not self.act_poke.is_fainted():
            all_moves = self.opp_poke.moves
        return all_moves

    def compute_score(self, heuristic: Heuristic, depth: int):
        score = heuristic.compute(self, depth)
        return score

    def simulate_action(self, move: Move | Pokemon, is_my_turn: bool):
        weather = None if len(self.weather.keys()) == 0 else next(iter(self.weather.keys()))
        if is_my_turn:

            if isinstance(move, Move):
                damage = compute_damage(move, self.act_poke.pokemon, self.opp_poke.pokemon, weather, self.terrains,
                                        self.opp_conditions, self.act_poke.boosts, self.opp_poke.boosts, is_my_turn)[
                    "lb"]

                if (move.accuracy is not True) and random.random() > move.accuracy:
                    damage = 0

                self.weather = self.get_active_weather(move, update_turn=False)
                updated_hp = self.opp_poke.current_hp - damage

                att_boost, def_boost = self.compute_updated_boosts(self.act_poke, self.opp_poke, move)

                opp_poke = self.opp_poke.clone(current_hp=updated_hp, boosts=def_boost)
                act_poke = self.act_poke.clone(boosts=att_boost)
                child = BattleStatus(act_poke, opp_poke,
                                     self.avail_switches, self.weather, self.terrains,
                                     self.opp_conditions, self, move)
            else:
                child = BattleStatus(NodePokemon(move, True, moves=list(move.moves.values())), self.opp_poke,
                                     self.avail_switches, self.weather, self.terrains,
                                     self.opp_conditions, self, move)
            return child

        else:
            damage = compute_damage(move, self.opp_poke.pokemon, self.act_poke.pokemon, weather, self.terrains,
                                    self.opp_conditions, self.opp_poke.boosts, self.act_poke.boosts, is_my_turn)["ub"]

            att_boost, def_boost = self.compute_updated_boosts(self.opp_poke, self.act_poke, move)
            updated_hp = self.act_poke.current_hp - damage
            act_poke = self.act_poke.clone(current_hp=updated_hp, boosts=def_boost)
            opp_poke = self.opp_poke.clone(boosts=att_boost)

            self.weather = self.get_active_weather(move, update_turn=True)

            return BattleStatus(act_poke, opp_poke,
                                self.avail_switches, self.weather, self.terrains,
                                self.opp_conditions, self, move)

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
    def compute_updated_boosts(att_poke: NodePokemon, def_poke: NodePokemon, move: Move):
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
                    # upd_stats_att = compute_stat_boost(att_poke.pokemon, stat_boost, boost)
                    # att_upd_boosts[stat_boost] = upd_stats_att
                    # upd_stats_def = compute_stat_boost(def_poke.pokemon, stat_boost, boost)
                    def_upd_boosts[stat_boost] += boost

        return att_upd_boosts, def_upd_boosts
