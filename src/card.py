
class Card:
    def __init__(self, card_id: str, color: str, num: int):
        self.num = num
        self.id = card_id
        self.wild = color == "wild" or color == ""
        self.color = color
    
    def get_color_name(self) -> str:
        color_map = {
            "R": "Red",
            "G": "Green", 
            "B": "Blue",
            "Y": "Yellow"
        }
        return color_map.get(self.color, "")

    def get_value(self) -> int:
        val = 0
        
        color_values = {
            "R": 100000,
            "G": 1000,
            "B": 100,
            "Y": 10000
        }
        val += color_values.get(self.color, 1000000)
        
        special_cards = {
            "SKIP": 10,
            "REVERSE": 11,
            "+2": 12,
            "WILD": 13,
            "WILD+4": 14
        }
        
        if self.id in special_cards:
            val += special_cards[self.id]
        else:
            try:
                card_num = int(self.id)
                val += card_num
            except ValueError:
                raise Exception("Invalid card found")
        
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