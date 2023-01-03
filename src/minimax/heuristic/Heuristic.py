from abc import ABC, abstractmethod


class Heuristic(ABC):

    def __init__(self):
        """
        Initialize the Heuristic class to define the evaluation function for the minimax algorithm
        """
        super(Heuristic, self).__init__()

    @abstractmethod
    def compute(self, battle_node, depth: int) -> float:
        pass
