class Card:
    def __init__(self, id: str, color: str = ""):
        self.__id = id
        self.__color = color
        self.__wild = color == ""

    def get_color_name(self) -> str:
        return {
            "R": "Red",
            "Y": "Yellow",
            "B": "Blue",
            "G": "Green",
        }[self.__color]
    
    def get_value(self) -> str:
        val = 0
        match self.__color:
            case "R":
                val += 100000    
            case "Y":
                val += 10000
            case "G":
                val += 1000
            case "B":
                val += 100
            case _:
                val + 1000000

        match self.__id:
            case 'SKIP':
                val += 10
            case 'REVERSE':
                val += 11
            case '+2':
                val += 12
            case 'WILD':
                val += 13
            case 'WILD+4':
                val += 14
            case _:
                val = int(self.__id)
        return val


    def __str__(self):
        if self.__color:
            return f"{self.get_color_name()} {self.__id}"

        return self.__id
           
    