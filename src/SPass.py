from .FPass import TMO, TIM, res_lines
from .LineParser import *
from .MyNum import MyNum


class Global(NamedTuple):
    vars: Dict[str, str]


class MacroGen(NamedTuple):
    name: str
    body: List[str]
    vars: Dict[str, str]


class MacroDef(NamedTuple):
    level: int


class If(NamedTuple):
    name: str
    vars: Dict[str, str]
    status: bool
    body: List[str]


class While(NamedTuple):
    name: str
    condition: str
    vars: Dict[str, str]
    status: bool
    body: List[str]
    copy_body: List[str]


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

    kargs = {**dict(macro_def.kargs), **dict(pl.kargs)}

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

        elif type(curr) is MacroGen or type(curr) is If or type(curr) is While:

            try:
                mg: MacroGen = curr
                line = mg.body.pop(0)
            except IndexError:
                stack.pop(-1)
                continue

            raw_line = line[:]
            line = insert_vars(line)

            pl = parse_line(line, TIM)

            if type(curr) is If:
                if type(pl) is MacroElse:
                    iff: If = stack.pop(-1)
                    stack.append(If(curr.name + '(else)', curr.vars, not curr.status, curr.body))
                    continue

                elif type(pl) is MacroEndif:
                    stack.pop(-1)
                    continue

                if not curr.status:
                    continue

            if type(curr) is While:
                if type(pl) is MacroWend:
                    whl: While = curr

                    vals = {}
                    for el in stack:
                        vals.update(el.vars)

                    _line = ' ' + whl.condition + ' '

                    if line.strip().__len__() == 0:
                        raise MacroError('-', f'No expression on if statement')

                    for k, v in vals.items():
                        _line = re.sub(rf'(?<=\W)\${k}(?=\W?|\Z)', f'MyNum({v.__repr__()})', _line, re.MULTILINE)

                    result = eval(_line)

                    stack.pop(-1)

                    if result:
                        stack.append(
                            While(whl.name, whl.condition, whl.vars, result,
                                  whl.copy_body[:], whl.copy_body)
                        )

                if not curr.status:
                    continue

            if type(pl) is MacroSet:
                ms: MacroSet = pl
                if not ms.arg.isidentifier():
                    raise MacroError(f'{curr.name} -> {raw_line.strip()}', f'{ms.arg} - wrong format for variable')

                if ms.arg[0] == '$':
                    raise MacroError(f'{curr.name} -> {raw_line.strip()}', f'variable names should not contain $.')

                curr.vars.update({ms.arg: ms.val})

            elif type(pl) is MacroInc:
                mi: MacroInc = pl

                vals = {}
                for el in stack:
                    if num := el.vars.get(mi.var):
                        try:
                            num = int(num)
                        except ValueError:
                            raise MacroError(f'{curr.name} -> {raw_line.strip()}', f'{num} - is not integer')
                        el.vars.update({mi.var: str(num + 1)})
                    vals.update(el.vars)

            elif type(pl) is MacroDec:
                mi: MacroDec = pl

                vals = {}
                for el in stack:
                    if num := el.vars.get(mi.var):
                        try:
                            num = int(num)
                        except ValueError:
                            raise MacroError(f'{curr.name} -> {raw_line.strip()}', f'{num} - is not integer')
                        el.vars.update({mi.var: str(num - 1)})
                    vals.update(el.vars)

            elif type(pl) is Command:
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
                        line = insert_vars(line)
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

            elif type(pl) is MacroIf:
                iff: MacroIf = pl

                vals = {}
                for el in stack:
                    vals.update(el.vars)

                _line = ' ' + raw_line.split(None, 1)[1] + ' '

                if _line.strip().__len__() == 0:
                    raise MacroError('-', f'No expression on if statement')

                for k, v in vals.items():
                    _line = re.sub(rf'(?<=\W)\${k}(?=\W?|\Z)', f'MyNum({v.__repr__()})', _line, re.MULTILINE)

                result = eval(_line)

                stack.append(If(stack[-1].name + f' > {raw_line.strip()}', {}, result, stack[-1].body))

            elif type(pl) is MacroWhile:
                whl: MacroWhile = pl

                vals = {}
                for el in stack:
                    vals.update(el.vars)

                _line = ' ' + raw_line.split(None, 1)[1] + ' '

                if line.strip().__len__() == 0:
                    raise MacroError('-', f'No expression on if statement')

                for k, v in vals.items():
                    _line = re.sub(rf'(?<=\W)\${k}(?=\W?|\Z)', f'MyNum({v.__repr__()})', _line, re.MULTILINE)

                result = eval(_line)

                stack.append(
                    While(stack[-1].name + f' > {raw_line.strip()}', raw_line.split(None, 1)[1], {}, result,
                          stack[-1].body, stack[-1].body[:])
                )

            elif type(pl) is Mend:
                pass

            elif type(pl) is MacroInv:
                macro_inv_handle(pl.name or '-', pl)

        elif type(curr) is If:
            pass

        elif type(curr) is While:
            pass


do_second_pass(res_lines)
print('\n'.join(i.strip() for i in output_lines))
print()

for k, (st, en) in TIM.items():
    print(f'{k}:')
    lines = TMO[st:en + 1]
    for line in lines:
        print(f'  {line}')
