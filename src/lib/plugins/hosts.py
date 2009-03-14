#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Alea-Soluciones (Bifer) 2007, 2008, 2009
# Licensed under GPL v3 or later, see COPYING for the whole text

'''
  $Id:$
  $URL:$
  Alea-Soluciones (Bifer) (c) 2007
  Created: stefan - 29/11/2007
'''


get_cli().set_privilege(privileges.NONE, privileges.CONFIGURE, 'bcli_hosts_del_ip_IP')
get_cli().set_privilege(privileges.NONE, privileges.CONFIGURE, 'bcli_hosts_del_name_STRING')
get_cli().set_privilege(privileges.NONE, privileges.CONFIGURE, 'bcli_hosts_add_IP_name_STRING')
get_cli().set_privilege(privileges.NONE, privileges.CONFIGURE, 'bcli_hosts_save_running')
get_cli().set_privilege(privileges.NONE, privileges.CONFIGURE, 'bcli_hosts_load_running')
get_cli().set_privilege(privileges.NONE, privileges.NORMAL, 'bcli_hosts_show_running')
get_cli().set_privilege(privileges.NONE, privileges.NORMAL, 'bcli_hosts')




hosts={}
hosts_filename="/etc/hosts"
#IPs and names that can't be deleted
protected_ips=['127.0.0.1']
protected_names=['localhost']

def get_ip_by_name(name):
    """look for name and return associated ip"""
    for ip, names in hosts.iteritems():
        if name in names:
            return ip

def hosts_load_config():
    """load host information from config file"""
    global hosts
    hosts={}
    file=open(hosts_filename,"r")
    for line in file.readlines():
        line=line.strip()
        if line=='' or line[0]=='#':
            continue
        
        names=line.split();

        hosts[names[0]]=names[1:]

#Initial load
hosts_load_config()

def bcli_hosts(line_words):
    """Host functionality for BOS systems.
    Call 'hosts save running' to save any changes made.
    Call 'hosts load running' to reload configuration from file (any changes made will be lost).
    """
    pass

def bcli_hosts_show_running(line_words):
    """Lists known hosts"""
    for ip, names in hosts.iteritems():
        print '%-16s '%(ip),
        for name in names:
            print '%-10s '%name,
        print ""
    
def bcli_hosts_add_IP_name_STRING(line_words):
    """Add a new host name"""
    ip=line_words[2]
    name=line_words[4]

    existinghost=get_ip_by_name(name)
    if existinghost==None:
        if hosts.has_key(ip):
            hosts[ip].append(name)
            print "Name added"
        else:
            hosts[ip]=[name]
            print "Host added"
    else:
        print "Hostname already exists for IP", existinghost
    
    
def bcli_hosts_load_running(line_words):
    """Reload configuration from file"""
    hosts_load_config()
    print "Configuration reloaded"
    

def bcli_hosts_del_ip_IP(line_words):
    """Delete host entry by IP"""
    ip=line_words[3]
    
    if ip in protected_ips:
        print "Error: IP",ip,"is protected"
        return
    
    if hosts.has_key(ip):
        del hosts[ip]
        print "Host with IP", ip, "deleted"
    else:
        print "IP",ip,"not found"

def bcli_hosts_del_name_STRING(line_words):
    """Delete host alias"""
    name=line_words[3]

    if name in protected_names:
        print "Error: Name",name,"is protected"
        return

    ip=get_ip_by_name(name)
    if ip==None:
        print "Name", name, "not found"
    else:
        hosts[ip].remove(name)
        print "Name", name, "deleted"
        if len(hosts[ip])==0:
            del hosts[ip]
            print "Entry", ip, "with no names automatically deleted"
            
        
def bcli_hosts_save_running(line_words):
    file=open(hosts_filename,"w")
    for ip, names in hosts.iteritems():
        file.write(ip+"\t")
        for name in names:
            file.write(name+" ")
        file.write("\n")
    print "Configuration saved"
