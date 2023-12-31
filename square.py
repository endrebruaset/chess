class Square:
    def __init__(self, row: int, column: int) -> None:
        self.row = row
        self.column = column
    
    def __eq__(self, __value: object) -> bool:
        return self.row == __value.row and self.column == __value.column
    
    def __hash__(self) -> int:
        return hash((self.row, self.column))
    
    def is_valid(self) -> bool:
        return 0 <= self.row < 8 and 0 <= self.column < 8