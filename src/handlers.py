from src.ui.main_w import Ui_MainWindow
from src.FPass import do_first_pass, TIM, TMO, res_lines
from src.SPass import stack, do_second_pass, output_lines, global_num
from src.exceptions import MacroError
from typing import *
from termcolor import colored


def cli_run(src: str):
    fpass = do_first_pass(src)

    while True:
        try:
            fpass.__next__()
        except StopIteration:
            break
        except MacroError as e:
            print(colored(str(e), 'red', attrs=['bold']))
            return

    spass = do_second_pass(res_lines)

    while True:
        try:
            spass.__next__()
        except StopIteration:
            break
        except MacroError as e:
            print(colored(str(e), 'red', attrs=['bold']))
            return

    return output_lines


def set_err(mw: Ui_MainWindow, s: str):
    mw.err.clear()
    mw.err.appendPlainText(s)


def set_tmo(mw: Ui_MainWindow):
    mw.TMO.clear()
    mw.TMO.appendPlainText('\n'.join(f'{str(i).zfill(2)}: {l}' for i, l in enumerate(TMO)))


def set_tim(mw: Ui_MainWindow):
    mw.TIM.clear()
    mw.TIM.appendPlainText('\n'.join(f'{k}: {st} ... {en}' for k, (st, en) in TIM.items()))


def set_vars(mw: Ui_MainWindow):
    mw.vars.clear()
    vals = {}
    for el in stack:
        mw.vars.appendPlainText('\n'.join(f'{k}: {v}' for k, v in el.vars.items()))
        mw.vars.appendPlainText(' ---- ---- ---- ')


def set_fp_res(mw: Ui_MainWindow):
    mw.fp_res.clear()
    mw.fp_res.appendPlainText('\n'.join(i[1] for i in res_lines))


def set_sp_res(mw: Ui_MainWindow):
    mw.sp_res.clear()
    mw.sp_res.appendPlainText('\n'.join(output_lines))


def setup_handlers(mw: Ui_MainWindow):
    with open('src/src.txt', 'r') as file:
        mw.src.appendPlainText(''.join(file.readlines()))

    fpass: Generator[None, None, None]
    spass: Generator[None, None, None]

    started = False
    started_2 = False
    finished_first = False
    finished_second = False
    blocked = False

    mw.one_step_btn_2.setEnabled(False)
    mw.all_btn_2.setEnabled(False)

    def one_step_btn_pressed():
        nonlocal fpass, started, finished_first, finished_second, blocked
        if blocked:
            return
        if not started:
            fpass = do_first_pass(mw.src.toPlainText())
            fpass.__next__()
            started = True

        try:
            fpass.__next__()
            set_tmo(mw)
            set_tim(mw)
            set_fp_res(mw)
        except StopIteration:
            finished_first = True
            mw.all_btn.setEnabled(False)
            mw.one_step_btn.setEnabled(False)
            mw.all_btn_2.setEnabled(True)
            mw.one_step_btn_2.setEnabled(True)
        except MacroError as e:
            blocked = True
            set_err(mw, str(e))
            mw.one_step_btn.setEnabled(False)
            mw.all_btn.setEnabled(False)

    mw.one_step_btn.pressed.connect(one_step_btn_pressed)

    def all_btn_pressed():
        while not blocked and not finished_first:
            one_step_btn_pressed()

    mw.all_btn.pressed.connect(all_btn_pressed)

    def one_step_btn_2_pressed():
        nonlocal spass, started_2, finished_first, finished_second, blocked
        if blocked:
            return
        if not started_2:
            spass = do_second_pass(res_lines)
            spass.__next__()
            started_2 = True

        try:
            spass.__next__()
            set_tmo(mw)
            set_tim(mw)
            set_sp_res(mw)
            set_vars(mw)

        except StopIteration:
            finished_second = True
            mw.all_btn.setEnabled(False)
            mw.one_step_btn.setEnabled(False)
            mw.all_btn_2.setEnabled(False)
            mw.one_step_btn_2.setEnabled(False)
        except MacroError as e:
            blocked = True
            set_err(mw, str(e))
            mw.one_step_btn_2.setEnabled(False)
            mw.all_btn_2.setEnabled(False)
    mw.one_step_btn_2.pressed.connect(one_step_btn_2_pressed)

    def all_btn_2_pressed():
        while not blocked and not finished_second:
            one_step_btn_2_pressed()

    mw.all_btn_2.pressed.connect(all_btn_2_pressed)

    def reset_btn_pressed():
        nonlocal fpass, started, finished_first, finished_second, blocked, started_2
        global TIM, TMO, res_lines, global_num
        mw.one_step_btn.setEnabled(True)
        mw.all_btn.setEnabled(True)
        mw.one_step_btn_2.setEnabled(False)
        mw.all_btn_2.setEnabled(False)
        mw.err.clear()
        mw.TIM.clear()
        mw.TMO.clear()
        mw.vars.clear()
        mw.fp_res.clear()
        mw.sp_res.clear()
        fpass = None
        started = False
        started_2 = False
        finished_first = False
        finished_second = False
        blocked = False
        global_num = -1
        TIM.clear()
        TMO.clear()
        res_lines.clear()
        stack.clear()
        output_lines.clear()

    mw.reset_btn.pressed.connect(reset_btn_pressed)
