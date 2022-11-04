from poke_env.environment import Pokemon, Battle
from poke_env.player import Player
from src.utilities.battle_utilities import compute_damage, outspeed_prob, compute_move_accuracy,\
    PROTECTING_MOVES, ENTRY_HAZARDS, ANTI_HAZARDS_MOVES


class RuleBasedPlayer(Player):

    verbose = False

    @staticmethod
    def __should_switch() -> bool:
        return False

    @staticmethod
    def __matchup() -> float:
        return 0

    @staticmethod
    def __should_dynamax(bot_pokemon: Pokemon, bot_team: list) -> bool:
        dynamax_p = False
        if len(bot_team) == 0:
            return True
        elif bot_pokemon.current_hp_fraction == 1:
            if len([pokemon for pokemon in bot_team if pokemon.current_hp_fraction == 1]) == 0:
                return True
            else:
                # Work with the matchup_score
                return False
        else:
            # Work with matchup_score
            return dynamax_p

    def choose_move(self, battle: Battle):
        # Retrieve both active pokèmon
        bot_pokemon: Pokemon = battle.active_pokemon
        opponent_pokemon: Pokemon = battle.opponent_active_pokemon

        # Retrieve weather and terrain
        weather = None if len(battle.weather.keys()) == 0 else next(iter(battle.weather.keys()))
        terrain = None if len(battle.fields.keys()) == 0 else next(iter(battle.fields.keys()))

        # Retrieve all the other pokèmon in the team that are still alive
        bot_team = [pokemon for pokemon in battle.team.values()
                    if pokemon is not bot_pokemon and not pokemon.fainted]

        # Compute matchup scores for every remaining pokèmon in the team
        bot_matchup = self.__matchup()
        team_matchups = [self.__matchup() for pokemon in bot_team]
        team_matchups = dict(zip(bot_team, team_matchups))

        # Switch out if there are available switches and the bot gains in terms of matchup by doing so
        if battle.available_switches and self.__should_switch():
            switch = max(team_matchups, key=lambda pokemon: team_matchups[pokemon])
            return self.create_order(switch)

        # Choose one available move
        if battle.available_moves:
            bot_moves = dict()
            for move in battle.available_moves:
                # If we don't know any move of the opponent, the matchup is slightly against, then use a protecting move
                if move.id in PROTECTING_MOVES and len(opponent_pokemon.moves) == 0 and bot_matchup < -1:
                    return self.create_order(move)

                # We can use a move that puts an entry hazard if it isn't already present
                opponent_team_size = 6 - len([pokemon for pokemon in battle.opponent_team.values() if pokemon.fainted])
                if move.id in ENTRY_HAZARDS and opponent_team_size >= 4\
                        and ENTRY_HAZARDS[move.id] not in battle.opponent_side_conditions:
                    return self.create_order(move)

                # We can remove any entry hazard on our side if we have enough pokèmon remaining on our team
                if move.id in ANTI_HAZARDS_MOVES and len(bot_team) >= 1 and len(battle.side_conditions) > 0:
                    return self.create_order(move)

                # if len(move.boosts) > 0 and bot_matchup >= 1:
                    # return self.create_order(move)

                # In any other case, compute the damage and accuracy of the move
                damage = compute_damage(move, bot_pokemon, opponent_pokemon, weather, terrain, True, self.verbose)
                accuracy = compute_move_accuracy(move, bot_pokemon, opponent_pokemon, weather, terrain, self.verbose)
                bot_moves.update({move: {"damage": damage, "accuracy": accuracy}})

            # Keep those moves with the max damage
            max_damage = max([damage_accuracy["damage"] for damage_accuracy in bot_moves.values()])
            max_damage_moves = {move: bot_move["accuracy"] for move, bot_move in bot_moves.items()
                                if bot_move["damage"] == max_damage}

            # Choose the move with the best accuracy
            best_move = max(max_damage_moves, key=lambda move_accuracy: max_damage_moves[move_accuracy])

            # Use the dynamax if convenient
            dynamax = False
            if battle.can_dynamax:
                dynamax = self.__should_dynamax(bot_pokemon, bot_team)

            return self.create_order(best_move, dynamax=dynamax)
        elif battle.available_switches:
            switch = max(team_matchups, key=lambda pokemon: team_matchups[pokemon])
            return self.create_order(switch)

        return self.choose_random_move(battle)
