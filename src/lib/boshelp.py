#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Alea-Soluciones (Bifer) 2007, 2008, 2009
# Licensed under GPL v3 or later, see COPYING for the whole text

'''
  $Id:$
  $URL:$
  Alea-Soluciones (Bifer) (c) 2007
  Created: eferro - 31/7/2007
'''


import boscli
import boscli.helpers
import boscli.boscliutils


def get_cmds():
    '''Return the command suported in the system. We consider a command (or
    a command family) the first word of a function'''
    functions = boscli.get_cli().get_functions()
    return sorted(list(set([a[0] for a in functions])))

def get_active_cmds():
    '''Return the command enable in the actual mode'''
    functions = boscli.get_cli().get_active_functions()
    return sorted(list(set([a[0] for a in functions])))

def get_functions(cmd):
    '''Return all the enabled functions that correspond to the comand indicated'''
    matchs = [a for a in boscli.get_cli().get_active_functions() if a[0] == cmd]
    return matchs


def bcli_help():
    """Commands for interactive help.
    """
    boscli.get_cli().basic_help()


def bcli_help_show_allcommands_full():
    """Show basic help for all availables commands (only for active mode).
    """
    cmd_list = []
    for cmd in boscli.get_cli().get_active_functions():
        str = ''
        str = str + boscli.get_cli().get_normalize_func_name(cmd)
        str = str + " => " + boscli.helpers.get_function_help(cmd).split('\n')[0]
        cmd_list.append(str)
    cmd_list.sort()
    for cmd in cmd_list: print(cmd)



def bcli_help_show_allcommands():
    """Show a list of all available commands (only for active mode).
    """
    cmd_list = []
    for cmd in boscli.get_cli().get_active_functions():
        cmd_list.append(boscli.get_cli().get_normalize_func_name(cmd))
    cmd_list.sort()
    for cmd in cmd_list:
        print(cmd)

def bcli_help_basic():
    '''Show basic help. Same as '?<tab>' at command lines
    '''
    boscli.get_cli().basic_help()

def bcli_help_command_CMD(cmd):
    '''Show short help of the (active) functions corresponding to the command expecified.
    The short help only contain a line with a general description of the command.
    '''
    if cmd not in get_active_cmds():
        print("There is no command named %s" % cmd)
    else:
        print(get_basic_help(cmd).strip())

def bcli_help_extended_command_CMD(cmd):
    '''Show extendeed help of the (active) functions corresponding to the command expecified.
    The extended help have all the info available at the BCli User Manual.
    '''
    if cmd not in get_active_cmds():
        print("There is no command named %s" % cmd)
    else:
        print(get_extended_help(cmd).strip())


def bcli_help_types():
    '''Show help for type/vars used in CLI commands.
    '''
    types = boscli.get_cli().get_type_names()
    types.sort()
    for t in types:
        print("%s => %s" % (t, boscli.get_cli().get_type(t).help()))

def get_basic_help(cmd):
    str = ""
    for func in get_functions(cmd):
        str = str + boscli.get_cli().get_normalize_func_name(func)
        str = str + " => " + boscli.helpers.get_function_help(func).split('\n')[0] + '\n'
    return str

def get_extended_help(cmd):
    str = ""
    for func in get_functions(cmd):
        str = str + boscli.get_cli().get_normalize_func_name(func)
        str = str + " => " + boscli.helpers.get_function_help(func) + '\n'
    return str



def bcli_remotehelp_connect():
    """Remote help mode related commands
    """
    pass


def bcli_remotehelp_act():
     """Activate remote help mode.
     """
     print("Starting remotehelp mode")
     print
     boscli.boscliutils.InteractiveCommand("screen -S bcli")


def bcli_remotehelp_connect():
     """Connect to an active remote help session.
     Use remotehelp act in other terminal to activate remote session.
     """
     boscli.boscliutils.InteractiveCommand("screen -x bcli")
