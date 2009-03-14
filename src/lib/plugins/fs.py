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

get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_fs_mkdir_STRING')
get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_fs_rmdir_STRING')
get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_fs_rm_FILE')
get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_fs')
get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_fs_less_FILE')
get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_fs_more_FILE')
get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_fs_dir')
get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_fs_ls')
get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_fs_cd_STRING')
get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_fs_mkdir_STRING')
get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_fs_rmdir_STRING')
get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_fs_rm_FILE')
get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_fs_pwd')
get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_fs_show_mount')
get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_fs_dir_ussage')
get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_fs_dir_ussage_STRING')
get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_fs_find_big_files')


def bcli_fs(line_words):
    """Commands for work with filesystem tree.
    """    
    pass


   
def bcli_fs_less_FILE(line_words):
    """Read content of file interactively
    """
    file = line_words[2]
    boscliutils.InteractiveCommand("less %s" % file)

bcli_fs_more_FILE = bcli_fs_less_FILE


    
def bcli_fs_dir(line_words):
    """List files at current directory.
The output format include the size, owner, permissions, size and name for
all the files."""
    boscliutils.InteractiveCommand("ls -l")

bcli_fs_ls = bcli_fs_dir

def bcli_fs_cd_STRING(line_words):
    """Change current dirirectory"""
    which_dir = line_words[2]
    os.chdir(which_dir)
    
def bcli_fs_mkdir_STRING(line_words):
    """Create directory"""
    which_dir = line_words[2]
    os.system("mkdir %s" %which_dir )
    
def bcli_fs_rmdir_STRING(line_words):
    """Remove directory"""
    which_dir = line_words[2]
    boscliutils.InteractiveCommand("rmdir %s" % which_dir )
    
def bcli_fs_rm_FILE(line_words):
    """Remove FILE"""
    file = line_words[2]
    boscliutils.InteractiveCommand("rm -i %s" % file)
 
def bcli_fs_pwd(line_words):
    """Show the current path"""
    boscliutils.InteractiveCommand("pwd")

def bcli_fs_show_mount(line_words):
    boscliutils.InteractiveCommand("mount | egrep -e '^/'")

def bcli_fs_dir_ussage(line_words):
    print "It may take some time"
    print "Ctrl-C to abort"
    boscliutils.InteractiveCommand("pwd")
    boscliutils.InteractiveCommand("du -s -h")

def bcli_fs_dir_ussage_STRING(line_words):
    print "It may take some time"
    print "Ctrl-C to abort"
    dir = line_words[3]
    boscliutils.InteractiveCommand("du -s -h %s 2>/dev/null" % dir)

    
def bcli_fs_find_big_files(line_words):
    """Show the top 10 bigger files from the current path
    """
    print "It may take some time"
    print "Ctrl-C to abort"
    boscliutils.InteractiveCommand("(find . -type f -exec ls -s \{} \; | sort -r -n | head -n 10) 2>/dev/null")
