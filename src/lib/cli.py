#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Alea-Soluciones (Bifer) 2007, 2008, 2009
# Licensed under GPL v3 or later, see COPYING for the whole text

'''
  $Id:$
  $URL:$
  Alea-Soluciones (Bifer) (c) 2007
  Created: eferro - 7/8/2007
'''



import boscliutils
import bostypes

get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_cli_exec_FILE')
get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_cli_reload')

class BiferShellAliasType(bostypes.BiferShellType):
    def __init__(self): 
        bostypes.BiferShellType.__init__(self)
    def values(self, incomplete_word):
        alias = []
        for a in get_cli().get_alias().keys():
            alias.append(a[1:])
        return alias

get_cli().add_type('ALIAS', BiferShellAliasType())


def bcli_cli(line_words):
    """Commands for interact with the BosCli itself.
    """    
    pass

def bcli_cli_pager(line_words):
    """Show if the pager is active or not.
    """
    if get_cli().pager() == True:
        print "Pager status: ON"
    else:
        print "Pager status: OFF"

def bcli_cli_pager_STATE(line_words):
    """Activate or Deactivate the command output pager.
    """
    state = line_words[2]
    if state in ['on', 'up']:
        get_cli().pager_on()
    else:
        get_cli().pager_off()
    
def bcli_cli_exec_FILE(line_words):
    """Execute a BosCli file.
    """
    get_cli().exec_cmds_file(line_words[2])
        
def bcli_cli_quit(line_words):
    """Exit from BosCli.
    """
    get_cli().quit()


def bcli_cli_history(line_words):
    """Show comand history.
    """
    print "Cmds history..."
    print
    num = 1
    while True:
        item = readline.get_history_item(num)
        if item == None:
            break
        print "%5d  '%s'" % (num, item)
        num = num + 1
                
def bcli_cli_history_clear(line_words):
    """Clear/Reset command history.
    """
    readline.clear_history()
    print "history cleared"

def bcli_cli_reload(line_words):
    """Reload all the functions registered at CLI.
    Only for internal use.
    """
    print "Reloading extensions"
    get_cli().init_commands()



def bcli_alias(line_words):
    """Commands for define alias.
    """    
    pass


def bcli_alias_list(line_words):
    """Show defined aliases and the corresponding values.
    """
    alias = get_cli().get_alias()
    for alias_name in alias.keys():
        print "%s => %s" % (alias_name, alias[alias_name])
        
def bcli_alias_define_STRING_STRING(line_words):
    """Define/Overwrite an alias.
    Set the value of the alias to the string especified as second argument. 
    """
    get_cli().add_alias('@' + line_words[2], line_words[3])
    print "%s => %s" % ('@' + line_words[2], line_words[3])
        
def bcli_alias_remove_ALIAS(line_words):
    """Remove the asigned value for an alias.
    """
    alias = '@' + line_words[2]
    if alias not in get_cli().get_alias().keys():
        print "%s not defined" % (alias)
    else:    
        get_cli().remove_alias(alias)
        print "%s removed" % (alias)

