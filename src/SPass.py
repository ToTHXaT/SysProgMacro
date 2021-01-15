from .FPass import TMO, TIM, res_lines
from .LineParser import *
from .MyNum import MyNum
from uuid import uuid4


class Global(NamedTuple):
    vars: Dict[str, str]


class MacroGen(NamedTuple):
    name: str
    body: List[str]
    vars: Dict[str, str]
    labels: Dict[str, str]


class MacroDef(NamedTuple):
    level: int


class If(NamedTuple):
    name: str
    vars: Dict[str, str]
    status: bool
    body: List[str]
    labels: Dict[str, str]
    level: int


class While(NamedTuple):
    name: str
    condition: str
    vars: Dict[str, str]
    status: bool
    body: List[str]
    copy_body: List[str]
    labels: Dict[str, str]
    iterations: Dict[str, int]


output_lines: List[str] = []
stack: List[Union[Global, MacroGen, MacroDef, If, While]] = []

global_num = -1


def assign_unique_label(label: str) -> str:
    global global_num
    global_num += 1
    return f'{label}_{global_num}'


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
        raise MacroError(i, f'Number of required positional parameters is not satisfied: Expected {macro_def.pargs.__len__()}, Got {pl.pargs.__len__()}')

    pargs = {}

    for ((arg_name, _), (val, _)) in zip(macro_def.pargs, pl.pargs):
        pargs[arg_name] = val

    diff = set(k[0] for k in pl.kargs) - set(k[0] for k in macro_def.kargs)

    if diff:
        raise MacroError(i, f'Unknown parameter `{", ".join(diff)}`')

    kargs = {**dict(macro_def.kargs), **dict(pl.kargs)}

    for k, v in kargs.items():
        if v is None:
            raise MacroError(i, f'{k} - argument not provided')

    args = {**pargs, **kargs}

    stack.append(MacroGen(pl.name, macro_body, args, {}))


def do_second_pass(src_lines: List[Tuple[int, str]]):
    ln_ind = 0
    tmo_ind = 0
    reg = False
    stack.append(Global({}))

    while True:
        yield

        curr = stack[-1]

        if type(curr) is Global:
            try:
                i, line = src_lines[ln_ind]
                ln_ind += 1
            except IndexError:
                break

            pl = parse_line(line, TIM)

            if type(pl) is Command:
                if m := re.findall(r'\$\w+', line, re.MULTILINE):
                    raise MacroError(f'{curr.name} -> {line}', f'{", ".join(m)} - unknown variables')

                if pl.args.__len__() == 1:
                    if pl.args[0] in curr.labels:
                        pl = Command(pl.label, pl.cmd, [curr.labels[pl.args[0]]])
                elif pl.args.__len__() == 2:
                    if pl.args[0] in curr.labels:
                        pl = Command(pl.label, pl.cmd, [curr.labels[pl.args[0]], pl.args[1]])
                    if pl.args[1] in curr.labels:
                        pl = Command(pl.label, pl.cmd, [pl.args[0], curr.labels[pl.args[1]]])

                output_lines.append(str(pl))

            elif type(pl) is MacroInv:

                macro_inv_handle(i, pl)
            else:
                raise MacroError(i, f'Innappropriate usage of {pl}')

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
                    if curr.level > 1:
                        continue
                    else:
                        iff: If = stack.pop(-1)
                        stack.append(If(curr.name + ' -> else', curr.vars, not curr.status, curr.body, {}, curr.level))
                        continue

                elif type(pl) is MacroEndif:
                    if curr.level > 1:
                        stack.pop(-1)
                        stack.append(If(curr.name, curr.vars, curr.status, curr.body, {}, curr.level - 1))
                    else:
                        stack.pop(-1)
                        continue
                elif type(pl) is MacroIf:
                    stack.pop(-1)
                    stack.append(If(curr.name, curr.vars, curr.status, curr.body, {}, curr.level + 1))

                if not curr.status:
                    continue

            elif type(curr) is While:
                if type(pl) is MacroWend:
                    whl: While = curr

                    vals = {}
                    for el in stack:
                        vals.update(el.vars)

                    _line = ' ' + whl.condition + ' '

                    if _line.strip().__len__() == 0:
                        raise MacroError(f'{curr.name} -> {raw_line.strip()}', f'No expression on while statement')

                    for k, v in vals.items():
                        _line = re.sub(rf'(?<=\W)\${k}(?=\W?|\Z)', f'MyNum({v.__repr__()})', _line, re.MULTILINE)

                    try:
                        result = eval(_line)
                    except Exception as e:
                        raise MacroError(f'{curr.name} -> {raw_line.strip()}', str(e))

                    stack.pop(-1)

                    if result:
                        if whl.iterations.get('num') == 1000:
                            raise MacroError(f'{curr.name} -> {raw_line.strip()}', f'Potentially infinite loop detected')
                        stack.append(
                            While(whl.name, whl.condition, whl.vars, result,
                                  whl.copy_body[:], whl.copy_body, {}, {'num': whl.iterations.get('num') + 1})
                        )
                    continue

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
                for el in stack[::-1]:
                    if num := el.vars.get(mi.var):
                        try:
                            num = int(num)
                        except ValueError:
                            raise MacroError(f'{curr.name} -> {raw_line.strip()}', f'{num} - is not integer')
                        el.vars.update({mi.var: str(num + 1)})
                        break
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
                if pl.label and (lbl := assign_unique_label(pl.label)):
                    curr.labels[pl.label] = lbl
                    pl = Command(lbl, pl.cmd, pl.args)

                if m := re.findall(r'\$\w+', line, re.MULTILINE):
                    raise MacroError(f'{curr.name} -> {line}', f'{", ".join(m)} - unknown variables')

                if pl.args.__len__() == 1:
                    if pl.args[0] in curr.labels:
                        pl = Command(pl.label, pl.cmd, [curr.labels[pl.args[0]]])
                elif pl.args.__len__() == 2:
                    if pl.args[0] in curr.labels:
                        pl = Command(pl.label, pl.cmd, [curr.labels[pl.args[0]], pl.args[1]])
                    if pl.args[1] in curr.labels:
                        pl = Command(pl.label, pl.cmd, [pl.args[0], curr.labels[pl.args[1]]])

                output_lines.append(str(pl))
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

                try:
                    _line = ' ' + raw_line.split(None, 1)[1] + ' '
                except IndexError:
                    raise MacroError(f'{curr.name} -> {raw_line.strip()}', f'No expression on if statement')

                if _line.strip().__len__() == 0:
                    raise MacroError('-', f'No expression on if statement')

                for k, v in vals.items():
                    _line = re.sub(rf'(?<=\W)\${k}(?=\W?|\Z)', f'MyNum({v.__repr__()})', _line, re.MULTILINE)

                try:
                    result = eval(_line)
                except Exception as e:
                    raise MacroError(f'{curr.name} -> {raw_line.strip()}', 'Type error')

                stack.append(If(stack[-1].name + f' -> {raw_line.strip()}', {}, result, stack[-1].body, {}, 1))

            elif type(pl) is MacroWhile:
                whl: MacroWhile = pl

                vals = {}
                for el in stack:
                    vals.update(el.vars)

                try:
                    _line = ' ' + raw_line.split(None, 1)[1] + ' '
                except IndexError:
                    raise MacroError(f'{curr.name} -> {raw_line.strip()}', f'No expression on while statement')

                if line.strip().__len__() == 0:
                    raise MacroError('-', f'No expression on if statement')

                for k, v in vals.items():
                    _line = re.sub(rf'(?<=\W)\${k}(?=\W?|\Z)', f'MyNum({v.__repr__()})', _line, re.MULTILINE)

                try:
                    result = eval(_line)
                except Exception as e:
                    raise MacroError(f'{curr.name} -> {raw_line.strip()}', str(e))

                stack.append(
                    While(stack[-1].name + f' -> {raw_line.strip()}', raw_line.split(None, 1)[1], {}, result,
                          stack[-1].body, stack[-1].body[:], {}, {'num': 1})
                )

            elif type(pl) is Mend:
                pass

            elif type(pl) is MacroInv:
                macro_inv_handle(curr.name + ' -> ' + raw_line.strip(), pl)
            elif type(pl):
                raise MacroError('-', f'Innappropriate usage of {pl}')

    if type(stack[-1]) is not Global:
        raise MacroError('-', 'Handling finished before quiting inner operation')
