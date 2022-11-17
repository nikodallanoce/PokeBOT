from typing import Optional

from poke_env import PlayerConfiguration, ServerConfiguration
from poke_env.player import Player
from poke_env.teambuilder import Teambuilder

from src.utilities.BattleStatus import BattleStatus
from src.utilities.Heuristic import Heuristic
from src.utilities.NodePokemon import NodePokemon
from src.utilities.battle_utilities import *
from src.utilities.stats_utilities import compute_stat
from src.utilities.SimpleHeuristic import SimpleHeuristic


class MiniMaxPlayer(Player):

    def __init__(self,
                 heuristic: Optional[Heuristic] = SimpleHeuristic(),
                 player_configuration: Optional[PlayerConfiguration] = None,
                 *,
                 avatar: Optional[int] = None,
                 battle_format: str = "gen8randombattle",
                 log_level: Optional[int] = None,
                 max_concurrent_battles: int = 1,
                 save_replays: Union[bool, str] = False,
                 server_configuration: Optional[ServerConfiguration] = None,
                 start_timer_on_battle_start: bool = False,
                 start_listening: bool = True,
                 ping_interval: Optional[float] = 20.0,
                 ping_timeout: Optional[float] = 20.0,
                 team: Optional[Union[str, Teambuilder]] = None,
                 ):
        super(MiniMaxPlayer, self).__init__(player_configuration=player_configuration, avatar=avatar,
                                            battle_format=battle_format, log_level=log_level,
                                            max_concurrent_battles=max_concurrent_battles, save_replays=save_replays,
                                            server_configuration=server_configuration,
                                            start_timer_on_battle_start=start_timer_on_battle_start,
                                            start_listening=start_listening,
                                            ping_interval=ping_interval, ping_timeout=ping_timeout, team=team)
        self.heuristic: Heuristic = heuristic

    def choose_move(self, battle):
        weather, terrains, bot_conditions, opp_conditions = retrieve_battle_status(battle).values()

        opp_max_hp = compute_stat(battle.opponent_active_pokemon, "hp", weather, terrains)
        root_battle_status = BattleStatus(
            NodePokemon(battle.active_pokemon, is_act_poke=True, moves=battle.available_moves),
            NodePokemon(battle.opponent_active_pokemon, is_act_poke=False, current_hp=opp_max_hp,
                        moves=list(battle.opponent_active_pokemon.moves.values())),
            battle.available_switches, weather, terrains,
            opp_conditions, None, Gen8Move('splash'))

        if battle.available_moves:
            # ris = self.minimax(root_battle_status, 2, True)  # notato che faceva mosse per recuperare vita e basta
            ris = self.alphabeta(root_battle_status, 2, float('-inf'), float('+inf'), True)
            node: BattleStatus = ris[1]
            best_move = self.choose_random_move(battle)  # il bot ha fatto U-turn e node diventava none
            if node is not None:
                best_move = node.move  # self.choose_random_move(battle)
                curr_node = node
                while curr_node.ancestor is not None:
                    best_move = curr_node.move
                    curr_node = curr_node.ancestor

                for mo in battle.available_moves:

                    damage = compute_damage(mo, battle.active_pokemon, battle.opponent_active_pokemon, weather,
                                            terrains, opp_conditions, True)["ub"]
                    chs_mv = mo.id + " : " + mo.type.name + " dmg: " + str(damage)
                    if mo.id == best_move.id:
                        chs_mv += "♦"
                    print(chs_mv)

                print()

            return self.create_order(best_move)
        elif battle.available_switches:
            return self.create_order(battle.available_switches[0])

        return self.choose_random_move(battle)

    def minimax(self, node: BattleStatus, depth: int, is_my_turn: bool) -> tuple[float, BattleStatus]:
        if depth == 0:
            score = node.compute_score(self.heuristic)
            node.score = score
            return node.score, node
        if is_my_turn:
            score = float('-inf')
            ret_node = node
            for poss_act in node.act_poke_avail_actions():
                new_state = node.simulate_action(poss_act, is_my_turn)
                child_score, child_node = self.minimax(new_state, depth, False)
                if score < child_score:
                    ret_node = child_node

                score = max(score, child_score)
                node.score = score
            return score, ret_node
        else:
            score = float('inf')
            ret_node = node
            for poss_act in node.opp_poke_avail_actions():
                new_state = node.simulate_action(poss_act, not is_my_turn)
                child_score, child_node = self.minimax(new_state, depth - 1, True)
                if score > child_score:
                    ret_node = child_node
                score = min(score, child_score)
                node.score = score
            return score, ret_node

    def alphabeta(self, node: BattleStatus, depth: int, alpha: float, beta: float, is_my_turn: bool) -> tuple[
        float, BattleStatus]:
        '''
        (* Initial call *) alphabeta(origin, depth, −inf, +inf, TRUE)
        '''
        if depth == 0:
            score = node.compute_score(self.heuristic)
            node.score = score
            return node.score, node
        if is_my_turn:
            score = float('-inf')
            ret_node = node
            for poss_act in node.act_poke_avail_actions():
                new_state = node.simulate_action(poss_act, is_my_turn)
                child_score, child_node = self.alphabeta(new_state, depth, alpha, beta, False)
                if score < child_score:
                    ret_node = child_node
                score = max(score, child_score)
                node.score = score

                if score >= beta:
                    break  # beta cutoff
                alpha = max(alpha, score)
            return score, ret_node
        else:
            score = float('inf')
            ret_node = node
            for poss_act in node.opp_poke_avail_actions():
                new_state = node.simulate_action(poss_act, not is_my_turn)
                child_score, child_node = self.alphabeta(new_state, depth - 1, alpha, beta, True)
                if score > child_score:
                    ret_node = child_node
                score = min(score, child_score)
                node.score = score

                if score <= alpha:
                    break  # alpha cutoff
                beta = min(beta, score)
            return score, ret_node
