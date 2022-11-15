from abc import ABC, abstractmethod

from src.utilities.BattleStatus import BattleStatus


class Heuristic(ABC):

    def __init__(self):
        super(Heuristic, self).__init__()

    @abstractmethod
    def compute(self, battle_node: BattleStatus) -> float:
        pass
