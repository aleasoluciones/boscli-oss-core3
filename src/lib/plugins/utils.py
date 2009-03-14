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
import privileges
import os
import os.path

__chrooted_user = "bos"


get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_util_editor')
get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_util_edit_FILE')
get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_util_seditor')
get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_util_seditor_FILE')

get_cli().set_privilege(privileges.ENABLE, privileges.NORMAL, 'bcli_util_serial_terminal')

# This functions are in manufacturer mode for security reasons
get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_util_tftp')
get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_util_ftp')




def bcli_util(line_words):
    """General utilities. Network clients, editors, and show on.
    """    
    pass

def bcli_util_editor(line_words):
    """Open a interactive editor"""
    boscliutils.InteractiveCommand("nano")
    
def bcli_util_edit_FILE(line_words):
    """Edit file"""
    file = line_words[2]
    boscliutils.InteractiveCommand("nano %s" % file)
    
def bcli_util_seditor(line_words):
    """Like "util editor", but at "next level" """
    boscliutils.InteractiveCommand("emacs")
    
    
def bcli_util_seditor_FILE(line_words):
    """Edit file, but with a great editor"""
    file = line_words[2]
    boscliutils.InteractiveCommand("emacs %s" % file)

    
def bcli_util_tracepath_IPHOST(line_words):
    """Show tracepath to the host
    """
    host = line_words[2]
    print "Press Ctrl-C to quit"
    print ""
    boscliutils.InteractiveCommand("tracepath %s" % host)


def bcli_util_mtr_IPHOST(line_words):
    """Show tracepath to the host with statistics of latency, packet loss, etc
    """
    host = line_words[2]
    print "Press Ctrl-C to quit"
    print ""
    boscliutils.InteractiveCommand("mtr %s" % host)

def lynx(url):
    """Text-based web-browser"""
    boscliutils.InteractiveCommand("lynx %s" % url)    

def bcli_util_lynx_IP(line_words):
    """Text-based web-browser"""
    lynx(line_words[2])

def bcli_util_lynx_WEBURL(line_words):
    """Text-based web-browser"""
    lynx(line_words[2])

def bcli_lynx_IP(line_words):
    """Text-based web-browser"""
    lynx(line_words[1])

def bcli_lynx_WEBURL(line_words):
    """Text-based web-browser"""
    lynx(line_words[1])

def bcli_util_tftp(line_words):
    """Interactive tftp client"""
    global __chrooted_user
    print "Use help to show commands for tftp client."
    print ""
    boscliutils.InteractiveCommand("sudo -u %s atftp" % __chrooted_user)

def bcli_util_ftp(line_words):
    """Interactive ftp client"""
    global __chrooted_user
    print "Use help to show commands for ftp client."
    print ""
    boscliutils.InteractiveCommand("sudo -u %s ncftp" % __chrooted_user)



def telnet(host, port):
    print "Press Ctrl-C to quit"
    print ""
    if port != None:
        boscliutils.InteractiveCommand("telnet %s %s" % (host, port))
    else:
        boscliutils.InteractiveCommand("telnet %s" % host)

def bcli_util_telnet_IPHOST(line_words):
    """Telnet client"""
    telnet(line_words[2], None)

def bcli_telnet_IPHOST(line_words):
    """Telnet client"""    
    telnet(line_words[1], None)


def bcli_util_telnet_IPHOST_INT(line_words):
    """Telnet client to the host and port specified"""
    telnet(line_words[2], line_words[3])

def bcli_telnet_IPHOST_INT(line_words):
    """Telnet client to the host and port specified"""
    telnet(line_words[1], line_words[2])

    
def bcli_util_ssh_IPHOST(line_words):
    """Conect to remote host using ssh.
Use example: ssh <host>
Run ssh client to conect to specified host using the 
default user <local user> and the default port <22>
    """
    host = line_words[2]
    boscliutils.InteractiveCommand("ssh %s" % (host))

def bcli_util_ssh_IPHOST_user_STRING(line_words):
    """Conect to remote host using ssh as a diferent user.
Use example: ssh <host> user <user>
Run ssh client to conect to specified host using the 
user specified and the default port <22>

    """
    host = line_words[2]
    user = line_words[4]
    boscliutils.InteractiveCommand("ssh %s@%s" % (user, host))

def bcli_util_ssh_IPHOST_port_INT(line_words):
    """Conect to remote host at the specified port.
Use example: ssh <host> port <port_num>
Run ssh client to conect to specified host using the 
default user <local user> and the port specified. Port 6922 
BOS enabled devices
    """
    host = line_words[2]
    port = line_words[4]
    boscliutils.InteractiveCommand("ssh -p %s %s" % (port, host))

def bcli_util_ssh_IPHOST_port_INT_user_STRING(line_words):
    """Conect to remote host/port using ssh as a diferent user.
Use example: ssh <host> port <port_number> user <user>
Run ssh client to conect to specified host using the 
user and port specified.

    """
    host = line_words[2]
    port = line_words[4]
    user = line_words[6]
    boscliutils.InteractiveCommand("ssh -p %s %s@%s" % (port, user, host))



def bcli_util_ping_broadcast_IPHOST(line_words):
    """Ping continuisly to the broadcast address.
The ping don't stop until Ctrl-C is pressed."""
    ip = line_words[3]
    print "Press Ctrl-C to quit"
    print ""
    boscliutils.InteractiveCommand("ping -b %s" % ip)


def bcli_ping_IPHOST(line_words):
    """Ping to a determinate IP address.
The ping don't stop until Ctrl-C is pressed."""
    ip = line_words[1]
    print "Press Ctrl-C to quit"
    print ""
    boscliutils.InteractiveCommand("ping %s" % ip)


def bcli_util_ping_IPHOST(line_words):
    """Ping to a determinate IP address.
The ping don't stop until Ctrl-C is pressed."""
    ip = line_words[2]
    print "Press Ctrl-C to quit"
    print ""
    boscliutils.InteractiveCommand("ping %s" % ip)

def bcli_util_serial_terminal(line_words):
    """Execute terminal client
    """
    print "Starting serial terminal client"
    boscliutils.InteractiveCommand("minicom -c on -t ansi -o")



def bcli_util_ipcalc_cidr_CIDR(line_words):
    """Show IP info from CIDR (netmask, min host, network adress, etc)
    """
    cidr = line_words[3]
    boscliutils.BatchCommand("ipcalc  -n -b " + cidr)

def bcli_util_ipcalc_IP_IP(line_words):
    """Show net address corresponding to the range specified
    """
    ip1 = line_words[2]
    ip2 = line_words[3]    
    boscliutils.BatchCommand("ipcalc  -n -b %s-%s" % (ip1, ip2))

def bcli_util_ipcalc_IP_mask_NETMASK(line_words):
    """Show IP info from IP / Netmask mask (netmask, min host, network adress, etc)
    """
    ip1 = line_words[2]
    mask = line_words[4]
    boscliutils.BatchCommand("ipcalc  -n -b %s %s" % (ip1, mask))

def bcli_util_nmap_net_CIDR(line_words):
    """Scan for hosts and ports in a network
    """
    cidr = line_words[3]
    boscliutils.BatchCommand("nmap %s" % (cidr))


def bcli_util_nmap_IPHOST(line_words):
    """Scan host for open ports (only tipical ports)
    """
    host = line_words[2]
    boscliutils.BatchCommand("nmap %s" % (host))


def bcli_util_nmap_IPHOST_port_INT(line_words):
    """Scan a port in a host
    """
    host = line_words[2]
    port = line_words[4]
    boscliutils.BatchCommand("nmap %s -p %s" % (host, port))


def bcli_util_nmap_IPHOST_portrange_INT_INT(line_words):
    """Scan a port range in a host
    """
    host = line_words[2]
    port1 = line_words[4]
    port2 = line_words[5]
    boscliutils.BatchCommand("nmap %s -p %s-%s" % (host, port1, port2))    

def bcli_util_diskled_activate(line_words):
    """Activate HD led. (Usefull to identify the server)
    """
    if os.path.exists("/dev/sda1"):
        print "Hard Disk led activated."
        print "Please use CTRL-C to stop"
        os.system("dd if=/dev/sda1 of=/dev/null 2>/dev/null")
        return
    if os.path.exists("/dev/hda1"):
        print "Hard Disk led activated."
        print "Please use CTRL-C to stop"        
        os.system("dd if=/dev/hda1 of=/dev/null 2>/dev/null")
        return

