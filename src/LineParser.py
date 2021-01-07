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


class MacroDef(NamedTuple):
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
    return bool(re.fullmatch(r"^\w+ macro( .*)+$", line, re.MULTILINE | re.IGNORECASE))


def is_mend(line: str) -> bool:
    return bool(re.fullmatch(r"^mend$", line))


def is_cmd(line: str) -> bool:
    try:
        return type(parse_line(line)) is Command
    except MacroError:
        return False


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
            raise MacroError('-', f'{arg} - invalid argument syntax')

        if spl.__len__() == 1:
            if was_keys:
                raise MacroError('-', f'{arg} - positional args cant appear after key args')
            arg = spl[0]
            def_val = None
            pargs.append((arg, def_val))
        elif spl.__len__() == 2:
            was_keys = True
            arg, def_val = spl
            kargs.append((arg, def_val))
        else:
            raise MacroError(0, f'Invalid - {arg}')

        if strict:
            if not arg.isidentifier():
                raise MacroError(0, f'Invalid name for argument {arg}')

    return pargs, kargs


def parse_macrodef(line: str, *, simple=False):

    label, _, args = line.split(' ', 2)

    if not label.isidentifier():
        raise MacroError(0, f'Invalid macro name {label}')

    if simple:
        return MacroDef(label, [], [])

    pargs, kargs = parse_params(args)

    return MacroDef(label, pargs, kargs)


class Command(NamedTuple):
    label: str
    cmd: str
    args: List[str]


class MacroInv(NamedTuple):
    name: str
    pargs: List[Tuple[str, Optional[str]]]
    kargs: List[Tuple[str, Optional[str]]]


def parse_line(line: str, TIM: Dict[str, Tuple[int, int]]) -> Union[MacroDef, Mend, Command, MacroInv]:
    if is_macrodef(line):
        return parse_macrodef(line)
    if is_mend(line):
        return Mend()

    try:
        line = line.strip()
        shl = shlex(line, posix=False)
        shl.whitespace += ','
        shl.wordchars += '-+?~!@#$%^&*='
        sp = list(shl)
    except Exception as e:
        raise Exception(e)

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

        raise MacroError('-', f'{label} - is neither a macro nor command')
