class Rule:
    def __init__(self, idx: int, desc: str, value: int, name: str, rtype: str, max_val: int, min_val: int):
        self.idx = idx
        self.desc = desc
        self.value = value
        self.name = name
        self.rtype = rtype
        self.max = max_val
        self.min = min_val

    def __str__(self):
        return f"*{self.name}*\nType: {self.rtype}\nValue: {self.value}\nRange: {self.min} to {self.max}\n{self.desc}"
