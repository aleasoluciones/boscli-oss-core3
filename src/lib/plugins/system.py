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
import re
import os
import privileges
import glob
import os.path


get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_util_editor')

get_cli().set_privilege(privileges.ENABLE, privileges.NORMAL, 'bcli_sys_reboot')
get_cli().set_privilege(privileges.ENABLE, privileges.NORMAL, 'bcli_sys_halt')


get_cli().set_privilege(privileges.ENABLE, privileges.CONFIGURE, 'bcli_sys_hostname_STRING')
get_cli().set_privilege(privileges.ENABLE, privileges.CONFIGURE, 'bcli_sys_update_boscli')
get_cli().set_privilege(privileges.ENABLE, privileges.CONFIGURE, 'bcli_sys_update_software')


logcat = '/opt/bifer/bin/bfr-logcat.py'
logdir = '/var/log'

class LogFileType(bostypes.BiferShellType):
    def __init__(self): 
        bostypes.BiferShellType.__init__(self)
        
    def values(self, incomplete_word):
        global logdir
        return [f.replace('/var/log/', '') for f in
                [f.strip() for f in os.popen('find /var/log -type f').readlines()]
                if f[-2:] != 'gz' and not f[-1:].isdigit()]
    
get_cli().add_type('LOGFILE', LogFileType())


def bcli_sys(line_words):
    """Commands for Shows/Change this host properties.
    """    
    pass

def bcli_sys_log_follow_LOGFILE(line_words):
    """Shows log file. Output appended data as the file grows
Show new log lines until Ctrl-C is pressed.
    """
    global logdir
    logfile = line_words[3]
    file = "%s/%s" % (logdir, logfile)
    if os.path.exists(file) and os.path.isfile(file):
        boscliutils.follow_file(file)
    else:
        print "The file %s is not a valid file" % file


def bcli_sys_log_show_LOGFILE_INT(line_words):
    """Dump log info corresponding a log file from INT number days ago until now.
    """
    global logdir
    global logcat
    logfile = line_words[3]
    days = line_words[4]
    file = "%s/%s" % (logdir, logfile)
    if os.path.exists(file) and os.path.isfile(file):
        boscliutils.BatchCommand("%s %s/%s %s" % (logcat, logdir, logfile, days))
    else:
        print "The file %s is not a valid file" % file

def bcli_sys_log_show_LOGFILE(line_words):
    """Dump log info corresponding a log file from two days ago until now.
    """
    global logdir
    global logcat
    logfile = line_words[3]
    file = "%s/%s" % (logdir, logfile)    
    if os.path.exists(file) and os.path.isfile(file):
        boscliutils.BatchCommand("%s %s/%s 2" % (logcat, logdir, logfile))
    else:
        print "The file %s is not a valid file" % file



def bcli_sys_date(line_words):
    """Show system date
    """
    boscliutils.BatchCommand("date")

def bcli_sys_show_version(line_words):
    """Show several version info about the system.
    """
    
    boscliutils.BatchCommand("uname -n")
    boscliutils.BatchCommand("uname -o")
    boscliutils.BatchCommand("uname -r -s")
    print
    print "GNU/Linux Distro flavour:"
    boscliutils.BatchCommand("cat /etc/lsb-release")
    print
    print "BosCli Version:", 
    boscliutils.BatchCommand("dpkg-query --show boscli-oss")
 

def bcli_sys_lastb(line_words):
    """show listing all bad login attempts.
    """
    boscliutils.BatchCommand("lastb")

def bcli_sys_reboot(line_words):
    """System reboot.
    Init a normal/safe reboot process. This action will be registered so it can be found using ''sys last'' command.     
    """
    if get_cli().confirm("Are you sure"):
        print "Sending reboot command..."
        print "Rebooting..."
        boscliutils.BatchCommand("reboot")    
    else:
        print "Command canceled"
        
def bcli_sys_halt(line_words):
    """System halt.
    Depending of the BIOS support this command can power off completely the system or only reach to the 
    halt state, waiting the user for the manual power off. 
    """
    if get_cli().confirm("Are you sure"):
        boscliutils.BatchCommand("halt")            
    else:
        print "Command canceled"
    
def bcli_sys_show_uptime(line_words):
    """Tell how long the system has been running.
    """
    boscliutils.BatchCommand("uptime")

def bcli_sys_show_mem(line_words):
    """Display amount of free and used memory in the system.
    Show the RAM, Swap and total memory ussage. The RAM is indicated in the "Mem:" line.
    Remember that ''shared'' indicate IPCv5 process shared memory, ''buffers'' and ''cached'' are kernel
    internal buffers used by linux to improve the overall system performance. 
    
    Buffers and Cached memory can be freeded by kernel to be used for user process without problem, so 
    in fact it can be consider as free memory. 
    """
    print "Note: All amount are expresed in Megabytes. ''Mem:'' line indicate RAM memory ussage"
    print
    boscliutils.BatchCommand("free -m -t")    



def bcli_sys_syslog(line_words):
    """Shows syslog messages. Output appended data as the file grows
Show new log lines until Ctrl-C is pressed.
    """
    boscliutils.follow_file('/var/log/syslog')


# Usefull aliases
bcli_sys_sl = bcli_sys_syslog
bcli_sl = bcli_sys_syslog

    
def bcli_sys_kernel_log(line_words):
    """Shows low level system log. Output appended data as the file grows
Show new log lines until Ctrl-C is pressed.
    """
    boscliutils.follow_file('/var/log/messages')

def bcli_sys_boot_log(line_words):
    """Shows kernel boot log.
Show low level boot messages.
    """
    boscliutils.BatchCommand("dmesg")

def bcli_sys_boot_log_reset(line_words):
    """Shows kernel boot log and clear it.
Show low level boot messages.
    """
    boscliutils.BatchCommand("dmesg -c")


def bcli_sys_top(line_words):
    """Run interactive processes monitor top
The top program periodically displays a list of processes on the system
in sorted order.  The default key for sorting is pid,  but other keys
can be used instead.  Various output options are available."""
    print "Press q to quit"
    print "Press h for help"
    boscliutils.InteractiveCommand("top")

def bcli_sys_htop(line_words):
    """Run interactive colorfull processes monitor htop
    """
    print "Press q to quit"
    print "Press h for help"
    boscliutils.InteractiveCommand("htop")
    
def bcli_sys_hostname(line_words):
    """Get hostname"""
    print socket.gethostname()
    
def bcli_sys_hostname_STRING(line_words):
    """Change the hostname"""
    new_hostname = line_words[2]
    old_hostname = socket.gethostname()
    if new_hostname == old_hostname:
        print "We all ready have this name"
    else:
        # Change the corresponging file
        
        open("/etc/hostname","w").write(new_hostname + '\n')
        hosts_lines = []
        for l in open("/etc/hosts","r").readlines():
            l = l.strip()
            if not l.startswith('127.0'): hosts_lines.append(l)
        hosts_file = open("/etc/hosts","w")
        hosts_file.write('127.0.0.1 localhost %s\n' % new_hostname)
        hosts_file.write('127.0.1.1 %s\n' % new_hostname)        
        for line in hosts_lines: hosts_file.write(line + '\n')
        hosts_file.close()
        boscliutils.BatchCommand("hostname %s" % new_hostname)
        print "New hostname %s" % socket.gethostname()
        

def bcli_sys_disk_ussage(line_words):
    """Report file system disk space usage.
    """
    boscliutils.BatchCommand("df -h")


def bcli_sys_update_boscli(line_words):
    """Force update of the boscli.
    """
    boscliutils.InteractiveCommand("apt-get update")
    boscliutils.InteractiveCommand("apt-get install -y --force-yes boscli-oss")

    
def bcli_sys_update_software(line_words):
    """Update the system software (including the CLI).
    """
    boscliutils.InteractiveCommand("apt-get update")
    boscliutils.InteractiveCommand("apt-get upgrade")



def bcli_check_system(line_words):
    """Run basic system check (system load, mem, HD)"""
    
    load_problem = "OK"
    load = float(open('/proc/loadavg').read().split()[1])
    if load >= 2.5: load_problem = "ERROR"
    print "%-8s %-40s" % (load_problem, 'CPU LOAD')
    
    # TODO: incluir el testeo de lo cacheado y en buffers para hacer la cuenta correcta
    mem_problem = "OK"
    mem_free = int((open('/proc/meminfo').read().split('\n')[1]).split()[1])
    if mem_free < 1000: mem_problem = "ERROR"
    print "%-8s %-40s" % (mem_problem, 'Mem free')
    
    hd_problem = "OK"
    text_hd_usage = os.popen("df -h").read()
    if re.search('\W9[5-9]%', text_hd_usage) != None: hd_problem = "ERROR"
    if re.search('\W100%', text_hd_usage) != None: hd_problem = "ERROR"
    print "%-8s %-40s" % (hd_problem, 'HD Occupation')
    
