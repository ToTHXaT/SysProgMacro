from .FPass import TMO, TIM, res_lines
from .LineParser import *


class Global(NamedTuple):
    vars: Dict[str, str]


class MacroGen(NamedTuple):
    name: str
    body: List[str]
    vars: Dict[str, str]


class MacroDef(NamedTuple):
    level: int


class If(NamedTuple):
    condition: str
    vars: Dict[str, str]


class While(NamedTuple):
    condition: str
    vars: Dict[str, str]


output_lines: List[str] = []
stack: List[Union[Global, MacroGen, MacroDef, If, While]] = []


def insert_vars(line: str):
    vals = {}
    for el in stack:
        vals.update(el.vars)

    for k, v in vals.items():
        line = re.sub(rf'(?<=\W)\${k}(?=\W?|\Z)', v, line, re.MULTILINE)

    return line


def macro_inv_handle(i, pl: MacroInv):
    st, en = TIM.get(pl.name)
    macro_head = TMO[st]
    macro_body = TMO[st + 1: en + 1]
    macro_def = parse_macrodef(macro_head)

    if not (macro_def.pargs.__len__() == pl.pargs.__len__()):
        raise MacroError(i, f'Number of required positional parameters is not satisfied')

    pargs = {}

    for ((arg_name, _), (val, _)) in zip(macro_def.pargs, pl.pargs ):
        pargs[arg_name] = val

    diff = set(k[0] for k in pl.kargs) - set(k[0] for k in macro_def.kargs)

    if diff:
        raise MacroError(i, f'Unknown parameter `{", ".join(diff)}`')

    kargs = {**dict(pl.kargs), **dict(macro_def.kargs)}

    for k, v in kargs.items():
        if v is None:
            raise MacroError(i, f'{k} - argument not provided')

    args = {**pargs, **kargs}

    stack.append(MacroGen(pl.name, macro_body, args))


def do_second_pass(src_lines: List[Tuple[int, str]]):
    ln_ind = 0
    tmo_ind = 0
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

                macro_inv_handle(i, pl)

            # elif type(pl) is Macro:
            #     if TIM.get(pl.name):
            #         raise MacroError(i, f'{pl.name} - macro name duplicate')
            #
            #     TIM[pl.name] = (TMO.__len__(), -1)
            #     TMO.append(line)
            #
            # elif type(pl) is Mend:
            #     pass

        elif type(curr) is MacroGen:
            try:
                mg: MacroGen = curr
                line = mg.body.pop(0)
            except IndexError:
                stack.pop(-1)
                continue

            line = insert_vars(line)

            pl = parse_line(line, TIM)

            if type(pl) is Command:
                output_lines.append(line)
            elif type(pl) is Macro:

                # lines: List[Tuple[int, str]] = list(yield_lines(src_lines))
                mg.body.insert(0, line)
                lines = mg.body
                md: Macro = Macro('', [], [])
                level = 0

                while True:
                    try:
                        line = lines[0]
                        i = mg.name
                    except IndexError:
                        break

                    if is_macrodef(line):
                        if level == 0:
                            md = parse_macrodef(line, simple=True)

                        level += 1

                        if level == 1:
                            if TIM.get(md.name):
                                raise MacroError(i, f'{md.name} - macro name duplicate')

                            TIM[md.name] = (TMO.__len__(), -1)

                        TMO.append(line)
                    elif is_mend(line):
                        level -= 1
                        if level == 0:
                            TIM[md.name] = (TIM.get(md.name)[0], TMO.__len__() - 1)
                            lines.pop(0)
                            break
                        else:
                            TMO.append(line)
                    else:
                        if level:
                            TMO.append(line)
                        else:
                            res_lines.append((i, line))

                    lines.pop(0)

            elif type(pl) is Mend:
                pass

            elif type(pl) is MacroInv:
                macro_inv_handle(pl.name or '-', pl)

        elif type(curr) is MacroDef:
            pass

        elif type(curr) is If:
            pass

        elif type(curr) is While:
            pass


do_second_pass(res_lines)
print('\n'.join(i.strip() for i in output_lines))

from pprint import pprint
pprint(TMO)
pprint(TIM)
