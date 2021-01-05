from .exceptions import *
from .LineParser import *


TMO: List[str] = []
TIM: Dict[str, Tuple[int, int]] = {}

_tmo = 0


def do_first_pass(src_lines: str):

    lines: List[Tuple[int, str]] = list(yield_lines(src_lines))

    line_ind = 0
    is_rec = False
    md: MacroDef = MacroDef('', [], [])
    res_lines: List[str] = []

    while True:
        try:
            i, line = lines[line_ind]
        except IndexError:
            break

        if is_macrodef(line):
            md = parse_macrodef(line, simple=True)
            is_rec = True

            if TIM.get(md.name):
                raise MacroError(i, f'{md.name} - macro name duplicate')

            TIM[md.name] = (TMO.__len__(), -1)
            TMO.append(line)
        elif is_mend(line):
            is_rec = False
            TIM[md.name] = (TIM.get(md.name)[0], TMO.__len__() - 1)
        else:
            if is_rec:
                TMO.append(line)
            else:
                res_lines.append(line)

        line_ind += 1


    from pprint import pprint
    pprint(TMO)
    pprint(TIM)
    pprint(res_lines)

with open('src/src.txt', 'r') as file:
    src = '\n'.join(file.readlines())
    do_first_pass(src)