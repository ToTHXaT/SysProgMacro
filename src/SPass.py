from .FPass import TMO, TIM, res_lines
from .LineParser import *


output_lines: List[str] = []
stack = []


class Global(NamedTuple):
    vars: Dict[str, str]


class MacroGen(NamedTuple):
    kargs: List[Tuple[str, None]]
    pargs: List[Tuple[str, str]]

    vars: Dict[str, str]


class MacroDef(NamedTuple):
    level: int


class If(NamedTuple):
    condition: str
    vars: Dict[str, str]


class While(NamedTuple):
    condition: str
    vars: Dict[str, str]


def do_second_pass(src_lines: List[Tuple[int, str]]):
    ln_ind = 0
    reg = False
    stack.append(Global({}))

    while True:

        curr = stack[-1]

        if type(curr) is Global:
            try:
                i, line = src_lines[ln_ind]
                ln_ind += 1
            except IndexError:
                break

            pl = parse_line(line, TIM)

            if type(pl) is Command:
                output_lines.append(line)

            elif type(pl) is MacroInv:
                st, en = TIM.get(pl.name)
                macro_def_line = TMO[st: en + 1]
                macro = parse_macrodef(macro_def_line[0])

                stack.append(MacroGen(macro.pargs, macro.kargs, {}))

            elif type(pl) is Macro:
                if TIM.get(pl.name):
                    raise MacroError(i, f'{pl.name} - macro name duplicate')

                TIM[pl.name] = (TMO.__len__(), -1)
                TMO.append(line)

            elif type(pl) is Mend:
                pass

        elif type(curr) is MacroDef:
            pass

        elif type(curr) is MacroInv:
            pass

        elif type(curr) is If:
            pass

        elif type(curr) is While:
            pass


do_second_pass(res_lines)
