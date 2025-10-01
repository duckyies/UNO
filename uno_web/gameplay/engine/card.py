from  gameplay.engine.constants import *

class Card:
    def __init__(self, card_id: str, color: str, num: int):
        self.num = num
        self.id = card_id
        self.wild = color == "wild" or color == ""
        self.color = color
    
    def get_color_name(self) -> str:
        return COLORS.get(self.color, "")

    def get_value(self) -> int:
        val = 0

        val += COLOR_VALUES.get(self.color, 1000000)
        
        if self.id in SPECIAL_CARDS:
            val += SPECIAL_CARDS[self.id]
        else:
            card_num = int(self.id)
            val += card_num
        
        return val
    
    def __str__(self) -> str:
        if self.wild:
            return self.id
        else:
            color_name = self.get_color_name()
            return f"{color_name} {self.id}"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Card):
            return False
        return self.get_value() == other.get_value()
    
    def __lt__(self, other) -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return self.get_value() < other.get_value()
    
    def __le__(self, other) -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return self.get_value() <= other.get_value()
    
    def __gt__(self, other) -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return self.get_value() > other.get_value()
    
    def __ge__(self, other) -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return self.get_value() >= other.get_value()