from abc import ABC, abstractmethod


class Heuristic(ABC):

    def __init__(self):
        super(Heuristic, self).__init__()

    @abstractmethod
    def compute(self, battle_node, depth: int) -> float:
        pass
