from typing import *
from shlex import shlex
from pydantic.dataclasses import dataclass
from .exceptions import MacroError
from .lists import reserved

import re


def yield_lines(src: str) -> Generator[Tuple[int, str], None, None]:
    for i, line in enumerate(src.replace('\n\n', '\n').split('\n'), start=1):
        sc = line.rfind(';')
        l1 = line.rfind("'")
        l2 = line.rfind('"')

        l = max(l1, l2)

        if sc > l:
            line = " ".join(line.rsplit(';', 1)[0].split())

        if line:
            yield i, line


def shlex_split(line: str, delim: str):
    try:
        line = line.strip()
        shl = shlex(line, posix=False)
        shl.whitespace = delim
        shl.wordchars += '-+?~!@#$%^&*='
        return list(shl)
    except Exception as e:
        raise Exception(e)


class Macro(NamedTuple):
    name: str
    pargs: List[Tuple[str, Optional[str]]]
    kargs: List[Tuple[str, Optional[str]]]

    def __str__(self):
        return self.name


class Mend(NamedTuple):
    pass


def remove_whitespaces(text: str):
    parts = re.split(r"""("[^"]*"|'[^']*')""", text)
    parts[::2] = map(lambda s: "".join(s.split()), parts[::2])
    return "".join(parts)


def is_macrodef(line: str):
    return bool(re.fullmatch(r"^\w+ macro(( .*)+$|$)", line.strip(), re.MULTILINE | re.IGNORECASE))


def is_mend(line: str) -> bool:
    return bool(re.fullmatch(r"^mend$", line.strip()))


def is_cmd(line: str) -> bool:
    try:
        return type(parse_line(line, {})) is Command
    except MacroError:
        return False


def is_if(line: str) -> bool:
    return bool(re.fullmatch(r"^if(( .*)+$|$)", line.strip(), re.MULTILINE | re.IGNORECASE))


def is_else(line: str) -> bool:
    return bool(re.fullmatch(r"^else$", line.strip()))


def is_endif(line: str) -> bool:
    return bool(re.fullmatch(r"^endif$", line.strip()))


def is_set(line: str) -> bool:
    return bool(re.fullmatch(r"^set [\w$]+ .+$", line.strip(), re.MULTILINE | re.IGNORECASE))


def is_while(line: str) -> bool:
    return bool(re.fullmatch(r"^while(( .*)+$|$)", line.strip(), re.MULTILINE | re.IGNORECASE))


def is_wend(line: str) -> bool:
    return bool(re.fullmatch(r"^wend$", line.strip()))


def is_inc(line: str) -> bool:
    return bool(re.fullmatch(r'^inc [\w$]+$', line.strip(), re.MULTILINE | re.IGNORECASE))


def is_dec(line: str) -> bool:
    return bool(re.fullmatch(r'^inc [\w$]+$', line.strip(), re.MULTILINE | re.IGNORECASE))


def parse_params(args: str, *, strict=True) -> Tuple[List[Tuple[str, None]], List[Tuple[str, str]]]:
    _args = remove_whitespaces(args)

    cmm = re.compile(r",(?=(?:[^\"']*[\"'][^\"']*[\"'])*[^\"']*$)")

    args_l = list(i.strip() for i in cmm.split(_args))

    pargs = []
    kargs = []

    was_keys = False

    for arg in args_l:

        spl = arg.split('=', 1)

        if spl[0].__len__ == 0:
            raise MacroError(f'{args}', f'`{arg}` - invalid argument syntax')

        if spl.__len__() == 1:
            if was_keys:
                raise MacroError(f'{args}', f'`{arg}` - positional args cant appear after key args')
            arg = spl[0]
            def_val = None
            pargs.append((arg, def_val))
        elif spl.__len__() == 2:
            was_keys = True
            arg, def_val = spl
            if def_val == '':
                def_val = None
            kargs.append((arg, def_val))
        else:
            raise MacroError(f'{args}', f'Invalid - `{arg}`')

        if strict:
            if not arg.isidentifier():
                raise MacroError(f'{args}', f'Invalid name for argument `{arg}`')

    return pargs, kargs


def parse_macrodef(line: str, *, simple=False):
    label, _, *args = line.split(None, 2)

    args = ''.join(args)

    if not label.isidentifier():
        raise MacroError(0, f'Invalid macro name `{label}`')

    if simple:
        return Macro(label, [], [])

    if not args:
        pargs = []
        kargs = []
    else:
        pargs, kargs = parse_params(args)

    return Macro(label, pargs, kargs)


class Command(NamedTuple):
    label: str
    cmd: str
    args: List[str]

    def __str__(self):
        return f'{self.label or ""} {self.cmd} {", ".join(self.args)}'


class MacroInv(NamedTuple):
    name: str
    pargs: List[Tuple[str, Optional[str]]]
    kargs: List[Tuple[str, Optional[str]]]


class MacroIf(NamedTuple):
    condition: str


class MacroElse(NamedTuple):
    pass


class MacroEndif(NamedTuple):
    pass


class MacroWhile(NamedTuple):
    condition: str


class MacroWend(NamedTuple):
    pass


class MacroSet(NamedTuple):
    arg: str
    val: str


class MacroInc(NamedTuple):
    var: str


class MacroDec(NamedTuple):
    var: str


def parse_line(line: str, TIM: Dict[str, Tuple[int, int]]) \
        -> Union[Macro, Mend, Command, MacroInv, MacroIf, MacroElse, MacroEndif,
                 MacroWhile, MacroWend, MacroSet, MacroInc, MacroDec]:
    if is_macrodef(line):
        return parse_macrodef(line)
    if is_mend(line):
        return Mend()
    if is_if(line):
        try:
            return MacroIf(line.split(None, 1)[1])
        except IndexError:
            return MacroIf('')
    if is_else(line):
        return MacroElse()
    if is_endif(line):
        return MacroEndif()
    if is_while(line):
        try:
            return MacroWhile(line.split(None, 1)[1])
        except IndexError:
            return MacroWhile('')
    if is_wend(line):
        return MacroWend()
    if is_set(line):
        _, arg, val = line.strip().split(None, 2)
        return MacroSet(arg, val)
    if is_inc(line):
        _, var = line.strip().split(None, 1)
        return MacroInc(var)
    if is_dec(line):
        _, var = line.strip().split(None, 1)
        return MacroDec(var)

    try:
        line = line.strip()
        shl = shlex(line, posix=False)
        shl.whitespace += ','
        shl.wordchars += '-+?~!@#$%^&*='
        sp = list(shl)
    except Exception as e:
        raise MacroError(f'{line}', f'{str(e)}')

    length = len(sp)

    if length == 0:
        pass
    elif length == 1:
        cmd = sp[0]

        if cmd in reserved:
            return Command(None, cmd, [])
        elif TIM.get(cmd):
            return MacroInv(cmd, [], [])
        else:
            raise MacroError('-', f'{cmd} - is neither a macro nor command')

    else:
        label, cmd, *args = sp

        if cmd in reserved:
            return Command(label, cmd, args)
        elif TIM.get(cmd):
            _, _, args = line.split(' ', 2)
            pargs, kargs = parse_params(args, strict=False)
            return MacroInv(cmd, pargs, kargs)

        cmd, *args = sp

        if cmd in reserved:
            return Command(None, cmd, args)
        elif TIM.get(cmd):
            _, args = line.split(' ', 1)
            pargs, kargs = parse_params(args, strict=False)
            return MacroInv(cmd, pargs, kargs)

        raise MacroError('-', f'{label} - Invalid line.')
