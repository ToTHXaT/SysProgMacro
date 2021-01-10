from .exceptions import MacroError


class MyNum:
    __slots__ = ('inn',)

    def __init__(self, val):
        try:
            self.inn = int(val)
        except:
            self.inn = val

    def __lt__(self, other):
        pass

    def __le__(self, other):
        return self < other or self == other

    def __gt__(self, other):
        pass

    def __ge__(self, other):
        return self > other or self == other

    def __eq__(self, other):
        tt = type(self.inn)
        ot = type(other)
        this = self.inn

        if tt is ot:
            return this == other

        if tt is str and ot is int:
            try:
                return ord(this) == other
            except:
                raise MacroError('-', f'')
        elif tt is int and ot is str:
            try:
                return str(this) == other
            except:
                raise MacroError('-', f'')
        else:
            raise MacroError('-', f'')

    def __ne__(self, other):
        return not self == other
