from abc import ABC, abstractmethod

class basePlayer(ABC):
    def __init__(self):
        self.onStart = []
        self.onGameEnd = []
        self.onTurnStart = []
        self.onHintColor = []
        self.onHintNumber = []
        self.onPlayerAction = []
    
    @abstractmethod
    def turn(self):
        pass
    