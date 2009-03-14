#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Alea-Soluciones (Bifer) 2007, 2008, 2009
# Licensed under GPL v3 or later, see COPYING for the whole text

'''
  $Id:$
  $URL:$
  Alea-Soluciones (Bifer) (c) 2007
  Created: eferro - 29/7/2007
'''



import re
import boscliutils


get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_kernel_set_KERNELVAR_STRING')
get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_kernel_ip_forward_STATE')
get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_kernel_spoof_protect_STATE')
get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_kernel_syncookies_STATE')
    
get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_kernel')
get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_kernel_show_KERNELVAR')
get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_kernel_list_all')
get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_kernel_list_kernel')
get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_kernel_list_dev')
get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_kernel_list_fs')
get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_kernel_list_net')
get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_kernel_list_vm')
get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_kernel_ip_forward')
get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_kernel_spoof_protect')
get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_kernel_syncookies')
 

    
    
   
def get_kernel_vars():
    return get_cli().type_values('KERNELVAR')
    
def get_variables(exp_reg):
    return sorted(list(set([a for a in get_kernel_vars() if re.match(exp_reg, a)])))

def set_kernel_values(var, value):
    boscliutils.BatchCommand("sysctl -w %s=%s" % (var, value))

def get_kernel_values(var):
    return os.popen("sysctl -n %s" % var).read().strip()

def bcli_kernel(line_words):
    """Comand for show/set low level kernel parameters.
    """    
    pass
    
def bcli_kernel_show_KERNELVAR(line_words):
    """Show the current value of a variable.
    Show the current value for the Kernel variable indicated.
    Use "kernel list all" or similar to see the known variables.
    """
    kernel_var = line_words[2]
    if kernel_var not in get_kernel_vars():
        print "'%s' is not a valid kernel var name" % kernel_var
        return
    print kernel_var
    print
    print get_kernel_values(line_words[2])
    
def bcli_kernel_list_all(line_words):
    """Show the actual kernel known variables.
    """
    for line in get_variables('.*'):
        print line

def bcli_kernel_list_kernel(line_words):
    """Show the known variables related with the Linux kernel itself.
    """
    
    for line in get_variables('^kernel.*'):
        print line

def bcli_kernel_list_dev(line_words):
    """Show the known variables related with the devices supported.
    """
    for line in get_variables('^dev.*'):
        print line

def bcli_kernel_list_fs(line_words):
    """Show the known variables related with the filesystems supported.
    """
    for line in get_variables('^fs.*'):
        print line

def bcli_kernel_list_net(line_words):
    """Show the known low level network parameters.
    """
    for line in get_variables('^net.*'):
        print line

def bcli_kernel_list_vm(line_words):
    """Show the known variables related with the virtual memory subsystem.
    """
    for line in get_variables('^vm.*'):
        print line
    
    
def bcli_kernel_set_KERNELVAR_STRING(line_words):
    """Set value for a low level kernel parameter.
    """
    kernel_var = line_words[2]
    value = line_words[3]
    if kernel_var not in get_kernel_vars():
        print "'%s' is not a valid kernel var name" % kernel_var
        return
    print "%s => %s" % (kernel_var, value)
    set_kernel_values(kernel_var, value)

def bcli_kernel_ip_forward_STATE(line_words):
    """Activate/Deactivate network forwarding at IP level (routing mode).
    """
    print "Ip forward activate %s" % line_words[2]
    if line_words[3] in ['on', 'up']:
        value = "1"
    else:
        value = "0"
    set_kernel_values("net.ipv4.ip_forward", value)

def bcli_kernel_ip_forward(line_words):
    """Show if network forwarding at IP level (routing mode) is enabled.
    """    
    if get_kernel_values("net.ipv4.ip_forward") == "1":
        print "On"
    else:
        print "Off"
    
def bcli_kernel_spoof_protect_STATE(line_words):
    """Activate/Deactivate Spoof protection (reverse-path filter) is enabled.
    Show ''kernel spoof protect'' help for further information.
    """
    print "Spoof protect %s" % line_words[2]
    if line_words[3] in ['on', 'up']:
        value = "1"
    else:
        value = "0"
    set_kernel_values("net.ipv4.conf.default.rp_filter", value)
    set_kernel_values("net.ipv4.conf.all.rp_filter", value)

def bcli_kernel_spoof_protect(line_words):
    """Show if Spoof protection (reverse-path filter) is enabled.
    The ''Spoof protect'' try to avoid the routing of bogus packets that can arrive from a machine using IP spoofing.
    Use a very simple system,  if the reply to this packet wouldn't go out the interface this packet came in, 
    then this is a bogus packet and should be ignored. This method don't avoid all IP spoofing practices.
    Normaly it should be enabled.
    """    
    if get_kernel_values("net.ipv4.conf.default.rp_filter") == "1":
        print "On"
    else:
        print "Off"
    
def bcli_kernel_syncookies_STATE(line_words):
    """Activate/Deactivate SYNC Cookies protection.
    Show ''kernel syncookies'' help for further information.
    """
    print "Sync Cookies %s" % line_words[1]
    if line_words[2] in ['on', 'up']:
        value = "1"
    else:
        value = "0"
    set_kernel_values("net.ipv4.tcp_syncookies", value)

def bcli_kernel_syncookies(line_words):
    """Show if SYNC Cookies protection is enabled.
    This avoid the clasical Sync flood DOS (Denial of Service) attack. Normaly it should be enabled.
    """
    if get_kernel_values("net.ipv4.tcp_syncookies") == "1":
        print "On"
    else:
        print "Off"

