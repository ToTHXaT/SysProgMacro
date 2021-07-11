from shlex import shlex
from typing import *


directives = [
    'byte',
    'word',
    'start',
    'end',
    'extref',
    'extdef',
    'csect'
]

registers = [f"r{i}" for i in range(16)]


def yield_lines(src: str) -> Generator[Tuple[int, str], None, None]:
    for i, line in enumerate(src.split('\n'), start=1):
        sc = line.rfind(';')
        l1 = line.rfind("'")
        l2 = line.rfind('"')

        l = max(l1, l2)

        if sc > l:
            line = " ".join(line.rsplit(';', 1)[0].split())

        if line:
            yield i, line


class Command(NamedTuple):
    label: str
    cmd: str
    args: List[str]


class Directive(NamedTuple):
    label: str
    dir: str
    args: List[str]


def handle_string(line: str, tko: TKO, i: int):
    i_of_1 = line.find('"')
    i_of_2 = line.find("'")

    if i_of_1 >= 0 and i_of_2 >= 0:
        lind = min(i_of_1, i_of_2)

    elif i_of_1 >= 0 > i_of_2:
        lind = i_of_1

    elif i_of_1 < 0 <= i_of_2:
        lind = i_of_2

    else:
        raise Exception("lineparser.check_string")

    ch = line[lind]

    rind = line.rfind(ch)

    if rind == -1 or rind == lind: raise Exception(f"[{i}]: No closing quotation")

    if line[rind + 1:] != "":
        raise Exception(f'[{i}]: Invalid string format')

    prm = line[lind:rind + 1]
    line = line[:lind] + line[rind + 1:]

    if ',' in line:
        raise Exception(f'[{i}]: Multiple arguments prohibited when defining strings')

    pl = parse_line(line, tko, i)

    # print(pl, prm, ch, lind, rind, line)

    directive = Directive(pl.label, pl.dir, [prm])
    if directive.dir != 'byte' and directive.dir != 'word':
        raise Exception(f'[{i}]: Invalid usage for string')

    return directive


def parse_line(line: str, tko: TKO, i: int) -> Union[Command, Directive]:
    if "'" in line or '"' in line:
        return handle_string(line, tko, i)

    try:
        line = line.replace(',', ' , ').strip()
        shl = shlex(line, posix=False)
        shl.whitespace += ','
        shl.wordchars += '-+?~!@#$%^&*'
        sp = list(shl)
    except Exception as e:
        raise Exception(e)

    length = len(sp)

    if length == 0:
        pass
    elif length == 1:
        cmd = sp[0]

        if is_cmd(cmd, tko):
            return Command(None, cmd, [])
        elif is_dir(cmd):
            return Directive(None, cmd.lower(), [])
        else:
            raise Exception(f'[{i}]: {cmd} is not an operation')

    else:
        label, cmd, *args = sp

        if is_cmd(cmd, tko):
            return Command(label, cmd, args)
        elif is_dir(cmd):
            return Directive(label, cmd.lower(), args)

        cmd, *args = sp

        if is_cmd(cmd, tko):
            return Command(None, cmd, args)
        elif is_dir(cmd):
            return Directive(None, cmd.lower(), args)

        raise Exception(f'[{i}]: Invalid line. `{args[0]}` is neither operation nor directive.')