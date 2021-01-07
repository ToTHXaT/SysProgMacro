from .FPass import TMO, TIM, res_lines
from .LineParser import *


output_lines: List[str] = []
stack = []


def macrogen():
    pass


def do_second_pass(src_lines: List[Tuple[int, str]]):
    ln_ind = 0
    reg = False
    level = 1

    while True:
        try:
            i, line = src_lines[ln_ind]
        except IndexError:
            break

        pl = parse_line(line, TIM)

        if type(pl) is Command:
            output_lines.append(line)

        elif type(pl) is MacroInv:
            pass#MacroGen

        elif type(pl) is MacroDef:
            if TIM.get(pl.name):
                raise MacroError(i, f'{pl.name} - macro name duplicate')

            TIM[pl.name] = (TMO.__len__(), -1)
            TMO.append(line)

        elif type(pl) is Mend:
            pass


do_second_pass(res_lines)
