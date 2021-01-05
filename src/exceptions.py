

class MacroError(Exception):

    def __init__(self, i, message):
        self.i = i
        self.message = message
        super().__init__(message)

    def __str__(self):
        return f'[{self.i}]: {self.message}'
