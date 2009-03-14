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


import boscliutils

__act_dns_info = {}


get_cli().set_privilege(privileges.NONE, privileges.CONFIGURE, 'bcli_dns_set_search_HOST')
get_cli().set_privilege(privileges.NONE, privileges.CONFIGURE, 'bcli_dns_set_nameserver_INT_IP')
get_cli().set_privilege(privileges.NONE, privileges.CONFIGURE, 'bcli_dns_clear')
get_cli().set_privilege(privileges.NONE, privileges.CONFIGURE, 'bcli_dns_save_running')
get_cli().set_privilege(privileges.NONE, privileges.CONFIGURE, 'bcli_dns_show_running')
get_cli().set_privilege(privileges.NONE, privileges.CONFIGURE, 'bcli_dns')
get_cli().set_privilege(privileges.NONE, privileges.NORMAL, 'bcli_dns')
get_cli().set_privilege(privileges.NONE, privileges.NORMAL, 'bcli_dns_show_running')
get_cli().set_privilege(privileges.NONE, privileges.NORMAL, 'bcli_dns')


num = 1
for line in open("/etc/resolv.conf").readlines():
    line = line.strip()
    if line.startswith("search "):
        __act_dns_info['search'] = line.split()[1]
        continue
    if line.startswith("nameserver "):
        __act_dns_info[num] = line.split()[1]
        num = num + 1

def dump_act_dns_info():
    global __act_dns_info
    str = ""
    nameservers = []
    try:
        str = str + "search %s\n" % __act_dns_info['search']
    except KeyError: pass
    for num in range(1, 4):
        try:
            if __act_dns_info[num] not in nameservers:
                str = str + "nameserver %s\n" % __act_dns_info[num]
                nameservers.append(__act_dns_info[num])
        except KeyError: continue        
    return str
    
 
def bcli_dns(line_words):
    """Commands for Show/Change dns resolver configuration
    """    
    pass 
    
# FIXME: realmente no tiene que ser host sino dominio
def bcli_dns_set_search_HOST(line_words):
    """Set the default domain to use.
    """
    global __act_dns_info
    __act_dns_info['search'] = line_words[3]
    
# FIXME: realmente no tiene que ser host sino dominio
def bcli_dns_set_nameserver_INT_IP(line_words):
    """Set a nameserver with the priority specified [1-3].
    Only support
    """
    global __act_dns_info
    try:
        prio = int(line_words[3])
    except ValueError, ex:
        print "'%s' isn't a valid priority (try with 1-3)" % line_words[3]
        return
    if prio not in range(1,4):
        print "'%s' isn't a valid priority (try with 1-3)" % line_words[3]
        return
    __act_dns_info[prio] = line_words[4]


def bcli_dns_show_running(line_words):
    """Show actual resolver configuration
    """
    str = dump_act_dns_info()
    if str == "":
        print "No actual dns resolv info"
    else:
        print str[:-1]
    

def bcli_dns_clear(line_words):
    """Clear all the resolver configuration.
    """
    global __act_dns_info
    __act_dns_info = {}


    
def bcli_dns_save_running(line_words):
    """Save the actual configuration for the next boot.
    """
    str = dump_act_dns_info()
    if str == "":
        print "There is no configuration"
    else:
        open("/etc/resolv.conf", "w").write(str)
        print "DNS resolv configuration saved"
        
    

