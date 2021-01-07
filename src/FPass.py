from .exceptions import *
from .LineParser import *


TMO: List[str] = []
TIM: Dict[str, Tuple[int, int]] = {}
res_lines: List[Tuple[int, str]] = []


def do_first_pass(src_lines: str):

    lines: List[Tuple[int, str]] = list(yield_lines(src_lines))

    line_ind = 0
    md: Macro = Macro('', [], [])
    level = 0

    while True:
        try:
            i, line = lines[line_ind]
        except IndexError:
            break

        if is_macrodef(line):
            md = parse_macrodef(line, simple=True)
            is_rec = True
            level += 1

            if TIM.get(md.name):
                raise MacroError(i, f'{md.name} - macro name duplicate')

            TIM[md.name] = (TMO.__len__(), -1)
            TMO.append(line)
        elif is_mend(line):
            level -= 1
            TIM[md.name] = (TIM.get(md.name)[0], TMO.__len__() - 1)
        else:
            if level:
                TMO.append(line)
            else:
                res_lines.append((i, line))

        line_ind += 1


with open('src/src.txt', 'r') as file:
    src = '\n'.join(file.readlines())
    do_first_pass(src)

    from pprint import pprint
    print()
    print(' ------ FIRST PASS ------ ')
    pprint(TMO)
    print()
    pprint(TIM)
    print()
    pprint(res_lines)
    print(' ****** FIRST PASS ****** ')
    print()
