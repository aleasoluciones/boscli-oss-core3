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



import boscli
import boscli.bostypes
import boscli.privileges

boscli.get_cli().set_privilege(boscli.privileges.MANUF, boscli.privileges.NORMAL, 'bcli_cli_exec_FILE')
boscli.get_cli().set_privilege(boscli.privileges.MANUF, boscli.privileges.NORMAL, 'bcli_cli_reload')

class BiferShellAliasType(boscli.bostypes.BiferShellType):
    def __init__(self): 
        boscli.bostypes.BiferShellType.__init__(self)
    def values(self, incomplete_word):
        alias = []
        for a in boscli.get_cli().get_alias().keys():
            alias.append(a[1:])
        return alias

boscli.get_cli().add_type('ALIAS', BiferShellAliasType())


def bcli_cli():
    """Commands for interact with the BosCli itself.
    """    
    pass

def bcli_cli_pager():
    """Show if the pager is active or not.
    """
    if boscli.get_cli().pager() == True:
        print "Pager status: ON"
    else:
        print "Pager status: OFF"

def bcli_cli_pager_STATE(state):
    """Activate or Deactivate the command output pager.
    """
    if state in ['on', 'up']:
        boscli.get_cli().pager_on()
    else:
        boscli.get_cli().pager_off()
    
def bcli_cli_exec_FILE(file):
    """Execute a BosCli file.
    """
    boscli.get_cli().exec_cmds_file(file)
        
def bcli_cli_quit():
    """Exit from BosCli.
    """
    boscli.get_cli().quit()


def bcli_cli_history():
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
                
def bcli_cli_history_clear():
    """Clear/Reset command history.
    """
    readline.clear_history()
    print "history cleared"

def bcli_cli_reload():
    """Reload all the functions registered at CLI.
    Only for internal use.
    """
    print "Reloading extensions"
    boscli.get_cli().init_commands()



def bcli_alias():
    """Commands for define alias.
    """    
    pass


def bcli_alias_list():
    """Show defined aliases and the corresponding values.
    """
    alias = boscli.get_cli().get_alias()
    for alias_name in alias.keys():
        print "%s => %s" % (alias_name, alias[alias_name])
        
def bcli_alias_define_STRING_STRING(alias_name, alias_value):
    """Define/Overwrite an alias.
    Set the value of the alias to the string especified as second argument. 
    """
    boscli.get_cli().add_alias('@' + alias_name, alias_value)
    print "%s => %s" % ('@' + alias_name, alias_value)
        
def bcli_alias_remove_ALIAS(alias_name):
    """Remove the asigned value for an alias.
    """
    alias = '@' + alias_name
    if alias not in boscli.get_cli().get_alias().keys():
        print "%s not defined" % (alias)
    else:    
        boscli.get_cli().remove_alias(alias)
        print "%s removed" % (alias)

