#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Alea-Soluciones (Bifer) 2007, 2008, 2009
# Licensed under GPL v3 or later, see COPYING for the whole text

'''
  $Id:$
  $URL:$
  Alea-Soluciones (Bifer) (c) 2007
  Created: eferro - 18/6/2008

  
'''



import os
import boscliutils
import bostypes


get_cli().set_privilege(privileges.ENABLE, privileges.NORMAL, 'bcli_monit_reload')
get_cli().set_privilege(privileges.ENABLE, privileges.NORMAL, 'bcli_monit_group_unmonitor_MONITGROUPTYPE')
get_cli().set_privilege(privileges.ENABLE, privileges.NORMAL, 'bcli_monit_group_monitor_MONITGROUPTYPE')
get_cli().set_privilege(privileges.ENABLE, privileges.NORMAL, 'bcli_monit_res_unmonitor_MONITNAMETYPE')
get_cli().set_privilege(privileges.ENABLE, privileges.NORMAL, 'bcli_monit_res_monitor_MONITNAMETYPE')


class BiferShellMonitNametype(bostypes.BiferShellType):
     def __init__(self): 
         bostypes.BiferShellType.__init__(self)
     def values(self, incomplete_word):
         monit_names = []
         for l in os.popen("monit summary").readlines()[1:]:
             try:
                 monit_names.append(l.split()[1].strip("'"))
             except:
                 pass
         monit_names.sort()
         return monit_names

class BiferShellMonitGrouptype(bostypes.BiferShellType):
     def __init__(self): 
         bostypes.BiferShellType.__init__(self)
     def values(self, incomplete_word):
         group_names = []
         group_names.append('all')
         for l in os.popen("grep -R group /etc/monit.d").readlines():
             try:
                 group_name = l.split()[2]
                 if  group_name not in group_names:
                     group_names.append(group_name)
             except:
                 pass
         group_names.sort()
         return group_names

    

get_cli().add_type('MONITNAMETYPE', BiferShellMonitNametype())
get_cli().add_type('MONITGROUPTYPE', BiferShellMonitGrouptype())




def bcli_monit(line_words):
    """Commands for interact with general monitoring system
    """
    pass

def bcli_monit_status(line_words):
    """Show summary status of all services/system parameters under monitoring.
    """
    print ""
    boscliutils.BatchCommand("monit summary")

def bcli_monit_status_loop(line_words):
    """Show summary status of all services/system parameters under monitoring (continuous loop).
    """
    boscliutils.InteractiveCommand("watch monit summary")

def bcli_monit_status_detailed(line_words):
    """Show detailed monitor system status.
    """    
    print ""
    boscliutils.BatchCommand("monit status")    


def bcli_monit_reload(line_words):
    """Reload monitoring configuration, and reinit monitoring process.
    """
    print 
    boscliutils.BatchCommand("monit reload")
    print 
    print "Please wait a few seconds and check the monitoring status"
    print "using 'monit status' or 'monit status loop'"

def monitoring_change_advise():
    print "Monitoring resorces change, use monit status to check resources under monitoring"

def bcli_monit_group_unmonitor_MONITGROUPTYPE(line_words):
    """Deactivate monitoring over all related resorces with the monit group specified.
    """
    print
    group = line_words[3]

    if group  not in   get_cli().get_type('MONITGROUPTYPE').values(''):
        print "Error: %s is not a valid monit group " % group
        return
    
    boscliutils.BatchCommand("monit unmonitor %s" % group)
    monitoring_change_advise()

def bcli_monit_group_monitor_MONITGROUPTYPE(line_words):
    """Activate monitoring over all related resorces with the monit group specified.
    """
    print
    group = line_words[3]

    if group  not in   get_cli().get_type('MONITGROUPTYPE').values(''):
        print "Error: %s is not a valid monit group " % group
        return
    
    boscliutils.BatchCommand("monit monitor %s" % group)
    monitoring_change_advise()


def bcli_monit_res_unmonitor_MONITNAMETYPE(line_words):
    """Deactivate moniting over the specified resource.
    """
    print
    resource = line_words[3]

    if resource  not in   get_cli().get_type('MONITNAMETYPE').values(''):
        print "Error: %s is not a valid monit resource " % resource
        return
    
    boscliutils.BatchCommand("monit unmonitor %s" % resource)
    monitoring_change_advise()

def bcli_monit_res_monitor_MONITNAMETYPE(line_words):
    """Activate moniting over the specified resource.
    """
    print
    resource = line_words[3]
    
    if resource  not in   get_cli().get_type('MONITNAMETYPE').values(''):
        print "Error: %s is not a valid monit resource " % resource
        return

    boscliutils.BatchCommand("monit monitor %s" % resource)
    monitoring_change_advise()

