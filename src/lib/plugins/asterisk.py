#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Alea-Soluciones (Bifer) 2007, 2008, 2009
# Licensed under GPL v3 or later, see COPYING for the whole text

'''
  $Id:$
  $URL:$
  Alea-Soluciones (Bifer) (c) 2007
  Created: eferro - 9/8/2007
'''



from pickle import FALSE

import bostypes
import os
import os.path
import glob
import boscliutils

__ast = 'asterisk'
__ast_ctl = 'asterisk -r'
__ast_rcmd = __ast_ctl + 'x'
__ast_cdr_file = '/var/log/asterisk/cdr-csv/Master.csv'

voicemail_dir = '/var/spool/asterisk/voicemail/default/'

class VoicemailNumbers(bostypes.BiferShellType):
    def __init__(self): 
        bostypes.BiferShellType.__init__(self)
    def values(self, incomplete_word):
        global voicemail_dir
        return [os.path.basename(d) for d in glob.glob('%s/*' % voicemail_dir)
                if os.path.isdir(d) and os.path.basename(d)[0].isdigit()]

get_cli().add_type('VOICEMAILNUMBER', VoicemailNumbers())


def check_asterisk_command_act():
    # TODO
    return True


def check_pri_act():
    cmd_out = asterisk_remote_cmd('pri show spans')
    if cmd_out.startswith("No such command"):
        print "Asterisk has no configured primary spans"
        return False
    else:
        return True


def asterisk_remote_cmd(cmd):
    global __ast_rcmd
    return os.popen(__ast_rcmd + '"%s"' % cmd).read()

class BiferShellAsteriskChanneltype(bostypes.BiferShellType):
    def __init__(self): 
        bostypes.BiferShellType.__init__(self)
    def values(self, incomplete_word):
        return ['chanuno', 'chandos']

class BiferShellAsteriskModulueType(bostypes.BiferShellType):
    def __init__(self): 
        bostypes.BiferShellType.__init__(self)
    def values(self, incomplete_word):
        return ['iax2', 'sip', 'mgcp'] 

get_cli().add_type('CHANNELTYPE', BiferShellAsteriskChanneltype())
get_cli().add_type('ASTMODULE', BiferShellAsteriskModulueType())


def bcli_asterisk(line_words):
    """Bifer Asterisk management functions
    """
    pass


def bcli_asterisk_noverbose(line_words):
    """Disable debug mode and verbose mode.
    """
    if check_asterisk_command_act():
        asterisk_remote_cmd('core set debug off')
        print "Debug off"
        asterisk_remote_cmd('set verbose 0')
        print "Disable level 0"
        
def bcli_asterisk_verbose(line_words):
    """Enable verbose mode.
    """
    if check_asterisk_command_act():
        asterisk_remote_cmd('set verbose 3')
        print "Verbose mode activated"

def bcli_asterisk_show_applications(line_words):
    """Show the currently loaded applications.
    """
    if check_asterisk_command_act():
        print asterisk_remote_cmd('core show applications')

def bcli_asterisk_show_functions(line_words):
    """Show the currently available functions.
    """
    if check_asterisk_command_act():
        print asterisk_remote_cmd('core show functions')

def bcli_asterisk_shell(line_words):
    """Connect to asterisk console.
    """
    if check_asterisk_command_act():
        global __ast_ctl
        boscliutils.InteractiveCommand(__ast_ctl)
        # sometimes asterisk console leve the terminal parameters 
        # corrupted. So yo reset the terminal...     
        boscliutils.InteractiveCommand("reset")

bcli_asterisk_cli = bcli_asterisk_shell

def bcli_asterisk_show_globals(line_words):
    """Show currently asterisk variables.
    """
    if check_asterisk_command_act():
        print asterisk_remote_cmd("core show globals")

def bcli_asterisk_show_channels(line_words):
    """Show configured channels.
    """
    if check_asterisk_command_act():
        print asterisk_remote_cmd("core show channels")

def bcli_asterisk_show_channeltypes(line_words):
    """Show supported channel types.
    """
    if check_asterisk_command_act():
        print asterisk_remote_cmd("core show channeltypes")

def bcli_asterisk_show_uptime(line_words):
    """Show process uptime.
    """
    if check_asterisk_command_act():
        print asterisk_remote_cmd("core show uptime")

def bcli_asterisk_show_version(line_words):
    """Show installed version.
    """
    if check_asterisk_command_act():
        global __ast
        boscliutils.InteractiveCommand(__ast + ' -V')

def bcli_asterisk_show_database(line_words):
    """Show all the internal asterisk database entries.
    """
    if check_asterisk_command_act():
        print asterisk_remote_cmd("database show")

def bcli_asterisk_show_dnd(line_words):
    """Show extensions with 'Do Not Disturb' activated.
    """
    if check_asterisk_command_act():
        print "Do not Disturb users"
        print asterisk_remote_cmd("database show DND")

def bcli_asterisk_show_cf(line_words):
    """Show extensions with 'Call Forward' or 'Call Forward on Busy' activated.
    """
    if check_asterisk_command_act():
        print "Call Forward and Call Forward on Busy entries"
        print asterisk_remote_cmd("database show CF")
        print asterisk_remote_cmd("database show CFB")
    
def bcli_asterisk_show_dialplan(line_words):
    """Show general dialplan.
    """
    if check_asterisk_command_act():
        print asterisk_remote_cmd("dialplan show")
        
def bcli_asterisk_reload_ASTMODULE(line_words):
    """Reload the specified module.
    """
    if check_asterisk_command_act():
        mod = line_words[2]
        print asterisk_remote_cmd("%s reload" % mod),
        print "%s reloaded" % mod

def bcli_asterisk_show_trunks(line_words):
    """Show trunks.
    Show the configurated trunks (output lines).        
    """
    if check_asterisk_command_act():
        print asterisk_remote_cmd('iax2 show peers')
        print asterisk_remote_cmd('sip show peers')

def bcli_asterisk_show_endpoints(line_words):
    """Show condfigurated endpoint.
    """
    if check_asterisk_command_act():
        print asterisk_remote_cmd('mgcp show lines')
        print asterisk_remote_cmd('mgcp show endpoints')
        print asterisk_remote_cmd('sip show peers')

def bcli_asterisk_voicemail_show_users(line_words):
    """Show users with voicemail activated.
    """
    if check_asterisk_command_act():
        print asterisk_remote_cmd('voicemail show users')


def bcli_asterisk_voicemail_del_VOICEMAILNUMBER(line_words):
    """Remove user voicemail voicemail (all messages)
    """
    if check_asterisk_command_act():
        if not get_cli().confirm("Are you sure"):
            print "Command canceled"
            return
        global voicemail_dir    
        vm = line_words[3]
        boscliutils.BatchCommand("rm -rf %s/%s" % (voicemail_dir, vm))
        print "Voicemail removed"

def bcli_asterisk_voicemail_reset_VOICEMAILNUMBER(line_words):
    """Return to default greeting message (remove the user defined)
    """
    if check_asterisk_command_act():
        global voicemail_dir    
        vm = line_words[3]
        boscliutils.BatchCommand("rm %s/%s/*.[Ww][Aa][Vv]" % (voicemail_dir, vm))
        print "Voicemail greeting reseted"


def bcli_asterisk_cdrs_show_all(line_words):
        """Show CDRs registered in the system.
            """
        if check_asterisk_command_act():
            global __ast_cdr_file
            print "Press Ctrl-C to quit"
            print ""
            boscliutils.BatchCommand("cat %s" % __ast_cdr_file)
            
def bcli_asterisk_cdrs_show_INT(line_words):
    """Show CDRs registered in the system.
    """
    if check_asterisk_command_act():
        global __ast_cdr_file
        num_lines = int(line_words[3])
        boscliutils.BatchCommand("tail -%d %s" % (num_lines, __ast_cdr_file))

def bcli_asterisk_cdrs_show_realtime(line_words):
    """Show CDRs in real time.
    """
    if check_asterisk_command_act():
        global __ast_cdr_file
        boscliutils.follow_file(__ast_cdr_file)

def bcli_asterisk_pri_show_channels_number(line_words):
    """Show the numbers of channels, (total, used and free)
    """
    num_channels = 0
    num_used_channels =	0
    if check_asterisk_command_act() and check_pri_act():
        for l in asterisk_remote_cmd('zap show channels').split('\n'):
            fields = l.split()
            if len(fields) == 4:
                if fields[0] != 'pseudo':
                    num_channels = num_channels	+ 1
                    if	fields[1] != 'from-pstn':
                         num_used_channels = num_used_channels + 1

    print "Channels: %d total, %d free, %d used" % (num_channels,
						    num_channels - num_used_channels,
	    	 	                            num_used_channels)



def bcli_asterisk_pri_show_channels(line_words):
    """Show primary spans channels
    """
    if check_asterisk_command_act() and check_pri_act():
	print  asterisk_remote_cmd('zap show channels')

def bcli_asterisk_pri_status_hardware(line_words):
    """Show status of the primary devices
    """
    if check_asterisk_command_act() and check_pri_act():
	print  asterisk_remote_cmd('zap show status')

def bcli_asterisk_pri_spans(line_words):
    """Show primary spans status
    """
    if check_asterisk_command_act() and check_pri_act():
	print  asterisk_remote_cmd('pri show spans')


def bcli_asterisk_dumptraf_sip_mta_IPHOST_eth_ETHIF(line_words):
    """Dump SIP traffic for a especified mta 
    """
    mta = line_words[4]
    eth = line_words[6]
    boscliutils.ngrep(eth, 5060, mta)

def bcli_asterisk_dumptraf_sip_mta_IPHOST(line_words):
    """Dump SIP traffic for a especified mta 
    """    
    mta = line_words[4]
    boscliutils.ngrep('eth0', 5060, mta)

def bcli_asterisk_dumptraf_mgcp_mta_IPHOST_eth_ETHIF(line_words):
    """Dump MGCP/NCS traffic for a especified mta 
    """        
    mta = line_words[4]
    eth = line_words[6]
    boscliutils.ngrep(eth, 2727, mta)
    
def bcli_asterisk_dumptraf_mgcp_mta_IPHOST(line_words):
    """Dump MGCP/NCS traffic for a especified mta 
    """            
    mta = line_words[4]
    boscliutils.ngrep('eth0', 2727, mta)
        
#-------------------------------------------


def bcli_asterisk_dumptraf_sip_mta_IPHOST_eth_ETHIF_byline(line_words):
    """Dump SIP traffic for a especified mta  (line by line mode)
    """
    mta = line_words[4]
    eth = line_words[6]
    boscliutils.ngrep_byline(eth, 5060, mta)

def bcli_asterisk_dumptraf_sip_mta_IPHOST_byline(line_words):
    """Dump SIP traffic for a especified mta  (line by line mode)
    """    
    mta = line_words[4]
    boscliutils.ngrep_byline('eth0', 5060, mta)

def bcli_asterisk_dumptraf_mgcp_mta_IPHOST_eth_ETHIF_byline(line_words):
    """Dump MGCP/NCS traffic for a especified mta  (line by line mode)
    """    
    mta = line_words[4]
    eth = line_words[6]
    boscliutils.ngrep_byline(eth, 2727, mta)
    
def bcli_asterisk_dumptraf_mgcp_mta_IPHOST_byline(line_words):
    """Dump SIP traffic for a especified mta  (line by line mode)
    """
    mta = line_words[4]
    boscliutils.ngrep_byline('eth0', 2727, mta)




