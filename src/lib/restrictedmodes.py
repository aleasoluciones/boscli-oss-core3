#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Alea-Soluciones (Bifer) 2007, 2008, 2009
# Licensed under GPL v3 or later, see COPYING for the whole text

'''
  $Id:$
  $URL:$
  Alea-Soluciones (Bifer) (c) 2008
  Created: eferro - 20/9/2008

'''


import boscliutils
import pickle
import os.path
import os
import time
import socket



def get_user_name():
    """Return the real user name based on the environ var"""
    # FIXME needs better implementation
    if os.environ.has_key("USERNAME"):
        return os.environ["USERNAME"]
    elif os.environ.has_key("SUDO_USER"):
        return os.environ["SUDO_USER"]
    else:
        return None


get_cli().set_privilege(privileges.NONE, privileges.CONFIGURE, 'bcli_passwd_configuremode')
get_cli().set_privilege(privileges.ENABLE, privileges.NORMAL, 'bcli_passwd_priv_enable')
get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_passwd_priv_manufacturer')



def bcli_passwd():
    """Change login password.
    """
    print "Changing system login password"
    boscliutils.InteractiveCommand("passwd %s" % get_user_name())

def bcli_passwd_configuremode():
    """Change configure mode access password.
    """
    get_cli().change_mode_passwd(privileges.CONFIGURE)

def bcli_passwd_priv_enable():
    """Change configure enable privilege level password.
    """
    get_cli().change_priv_passwd(privileges.ENABLE)

def bcli_passwd_priv_manufacturer():
    """Change configure manufacturer privilege level password.
    """
    get_cli().change_priv_passwd(privileges.MANUF)


    
def validate_change_mode(mode):
    """If the is not a password defined return false,
    in other cases, prompt the user for password and return if
    the introduced passwd is correct. If password defined is
    empty don't ask the user for pass"""
    #FIXME
    try:
        global passwords
        
        try:
            password = passwords[mode]
        except KeyError:
            return False
        if password == '':
            return True

        passwd = get_password()
        if passwd ==  password or passwd in get_temp_passwords():
            return True
        else:
            return False
    except:
        # If we have any problem allways return that the password
        # is not ok.
        return False





#---------------------------------------------------------------------------------
# Functions for change privileges:
#   enable
#   disable
#   manufacturer
get_cli().set_privilege(privileges.ENABLE, privileges.NORMAL, 'bcli_disable')

def bcli_enable():
    """Change privileges to enable level (level 1)
    """
    get_cli().change_priv(privileges.ENABLE)


def bcli_manufacturer():
    """Change privileges to manufacturer level (level 2)
    """
    get_cli().change_priv(privileges.MANUF)

def bcli_disable():
    """Change privileges to 0 (initial level)
    """
    get_cli().change_priv(privileges.NONE)
#---------------------------------------------------------------------------------



#---------------------------------------------------------------------------------
# Functions for change modes (NORMAL, CONFIGURE):
#   configure
#   normal
get_cli().set_privilege(privileges.NONE, privileges.CONFIGURE, 'bcli_normal')

def bcli_configure():
    """Change mode to configuremode
    """
    get_cli().change_mode(privileges.CONFIGURE)

# Usefull for users with cisco cli addiction
bcli_configure_terminal = bcli_configure

def bcli_normal():
    """Change mode to normal
    """
    get_cli().change_mode(privileges.NORMAL)
#---------------------------------------------------------------------------------


#---------------------------------------------------------------------------------
def bcli_exit():
    """Exit from configure mode or from CLI (if we are at NORMAL mode).
    """
    if get_cli().get_mode() == privileges.NORMAL:
        get_cli().quit()
    else:
        print "Exit from actual mode..."
        get_cli().change_mode(privileges.NORMAL)
#---------------------------------------------------------------------------------




#---------------------------------------------------------------------------------
get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_privilege_initial_enable')
get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_privilege_initial_manufacturer')
get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_privilege_initial_normal')

def bcli_privilege_initial_enable():
    """Set enable level as initial privilege level for actual user
    """
    get_cli().change_initial_privilege(privileges.ENABLE)
    print "Inital user privileges change to: 1 [enable level]"

def bcli_privilege_initial_manufacturer():
    """Set manufacturer level as initial privilege level for actual user
    """
    get_cli().change_initial_privilege(privileges.MANUF)
    print "Inital user privileges change to: 2 [manufacturer level]"

def bcli_privilege_initial_normal():
    """Set normal level as initial privilege level for actual user
    """
    get_cli().change_initial_privilege(privileges.NONE)
    print "Inital user privileges change to: 0 [normal level]"
#---------------------------------------------------------------------------------

    
