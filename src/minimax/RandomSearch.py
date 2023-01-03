import random
from typing import Tuple
from poke_env.player import Player, cross_evaluate, baselines
from src.minimax.heuristic.TeamHeuristic import TeamHeuristic
from poke_env import PlayerConfiguration
from src.players.MiniMaxPlayer import MiniMaxPlayer


class RandomSearch:

    def __init__(self,
                 bot_name: str = "MM",
                 heuristic: TeamHeuristic = TeamHeuristic(),
                 max_depth: int = 2,
                 benchmark: Player = baselines.SimpleHeuristicsPlayer(
                     player_configuration=PlayerConfiguration("baseline", None)),
                 n_matches: int = 100,
                 parameters_range: Tuple[float, float] = (0, 1),
                 penalty_range: Tuple[float, float] = (0, 0.05),
                 ):
        self.bot_name: str = bot_name
        self.max_depth: int = max_depth
        self.opp_name: str = benchmark.username
        self.n_matches: int = n_matches
        self.benchmark: Player = benchmark
        self.parameters_num: int = heuristic.parameters_num
        self.parameters_range: Tuple[float, float] = parameters_range
        self.penalty_range: Tuple[float, float] = penalty_range

    async def compute(self, num_config: int = 10):
        # Dummy initialization
        max_ = float("-inf")
        best_parameters = [random.uniform(self.parameters_range[0], self.parameters_range[1]) for _ in
                           range(self.parameters_num)]
        best_penalty = random.uniform(self.penalty_range[0], self.penalty_range[1])
        bot_players = 0

        for config in range(num_config):
            parameters = [random.uniform(self.parameters_range[0], self.parameters_range[1]) for _ in
                          range(self.parameters_num)]
            penalty = random.uniform(self.penalty_range[0], self.penalty_range[1])

            # Normalize
            sum_parameters = sum(parameters)
            parameters = [x / sum_parameters for x in parameters]

            heuristic = TeamHeuristic(parameters=parameters, penalty=penalty)
            player = MiniMaxPlayer(player_configuration=PlayerConfiguration(self.bot_name + str(bot_players), None),
                                   heuristic=heuristic, max_depth=self.max_depth)
            cross_evaluation = await cross_evaluate([player, self.benchmark], n_challenges=self.n_matches)
            # print(cross_evaluation)
            value = cross_evaluation[self.bot_name + str(bot_players)][self.opp_name]
            print(value)
            if value > max_:
                max_ = value
                best_parameters = parameters
                best_penalty = penalty
            bot_players += 1

        # print(max_)
        print(best_parameters)
        print(best_penalty)

        return best_parameters, best_penalty
