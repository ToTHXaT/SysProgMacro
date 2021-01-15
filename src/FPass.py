from .exceptions import *
from .LineParser import *
from src.lists import reserved


TMO: List[str] = []
TIM: Dict[str, Tuple[int, int]] = {}
res_lines: List[Tuple[int, str]] = []


def do_first_pass(src_lines: str):

    lines: List[Tuple[int, str]] = list(yield_lines(src_lines))

    line_ind = 0
    md: Macro = Macro('', [], [])
    level = 0

    while True:
        yield
        try:
            i, line = lines[line_ind]
        except IndexError:
            break

        if is_macrodef(line):
            if level == 0:
                md = parse_macrodef(line, simple=True)
                is_rec = True

            level += 1

            if level == 1:
                if TIM.get(md.name):
                    raise MacroError(i, f'`{md.name}` - macro name duplicate')
                if md.name in reserved:
                    raise MacroError(i, f'`{md.name}` - this name is reserved')
                if not md.name.isidentifier():
                    raise MacroError(i, f'`{md.name}` - invalid name')

                TIM[md.name] = (TMO.__len__(), -1)

            TMO.append(line)
        elif is_mend(line):
            level -= 1
            if level < 0:
                raise MacroError(i, 'inapropriate usage of mend')
            if level == 0:
                is_rec = False
                TIM[md.name] = (TIM.get(md.name)[0], TMO.__len__() - 1)
            else:
                TMO.append(line)
        else:
            if level:
                TMO.append(line)
            else:
                res_lines.append((i, line))

        line_ind += 1

    if level > 0:
        raise MacroError('-', f'mend is missing for {md.name}')

