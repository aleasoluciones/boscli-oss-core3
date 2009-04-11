#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Alea-Soluciones (Bifer) 2007, 2008, 2009
# Licensed under GPL v3 or later, see COPYING for the whole text

'''
  $Id:$
  $URL:$
  Alea-Soluciones (Bifer) (c) 2007
  Created: eferro - 22/7/2007
'''    


import socket
import re
import bosip
import os
import boscliutils
import glob
    
class BiferShellTypeManager:
    def __init__(self):
        self.types = {
            'STRING': BiferShellString(),
            'BOOL': BiferShellBool(),
            'STATE': BiferShellState(),
            'INT': BiferShellInt(),
            'FLOAT': BiferShellFloat(),
            'NET': BiferShellNet(),
            'NETMASK': BiferShellNetMask(),
            'NETIF': BiferShellNetIf(),
            'MAC': BiferShellMac(),
            'IP': BiferShellIp(),
            'CIDR': BiferShellCidr(),
            'HOST': BiferShellHost(),
            'IPHOST': BiferShellIpHost(),
            'WEBURL': BiferShellWebUrl(),
            'FILE': BiferShellFile(),
            'CMD': BiferShellCmd(),
            'KERNELVAR': BiferShellKernelVar(),
            'HEXNUMBER': BiferShellHexNumber(),
        }
    
    def add_type(self, type_name, type_class_instance):
        self.types[type_name] = type_class_instance

    def get_types(self):
        return self.types.keys()
        
    def get_type(self, type_name):
        return self.types[type_name]
    
    def set_cli(self, cli):
        for type in self.types.keys():
            self.types[type].set_cli(cli)
            
    def validate_value(self, type, value):
        return self.types[type].validate_value(value)
    def normalize(self, type, value):
        return self.types[type].normalize(value)
    def values(self, type, incomplete_word):
        return self.types[type].values(incomplete_word)
    def is_type(self, word):
        return word in self.types.keys()         
    
class BiferShellType:
    def __init__(self, doc = "Doc to be defined"):
        self.cli = None
        self.doc = doc

    def set_cli(self, cli):
        self.cli = cli
        
    def validate_value(self, value):
        res = value in self.values('')
        return res
    
    def normalize(self, value):
        return value
    
    def values(self, incomplete_word):
        return []

    def help(self):
        return self.doc
    
class BiferShellString(BiferShellType):
    def __init__(self): 
        BiferShellType.__init__(self, "Sequence of letters, digits or '_'. Ex: Xema")
    
    def validate_value(self, value):
        return True
    
    def normalize(self, value):
        return value.strip()
    
class BiferShellIp(BiferShellType):
    def __init__(self): 
        BiferShellType.__init__(self, "IP Address in dot-decimal notation: Ex: 192.168.1.100")
    def validate_value(self, value):
        try:
            if len(value.split('.')) != 4: return False

            mm = socket.inet_aton(value)
            return True # We got through that call without an error, so it is valid
        except socket.error:
            return False # There was an error, so it is invalid

class BiferShellHost(BiferShellType): 
    def __init__(self): 
        BiferShellType.__init__(self, "Hostname. Ex: www.google.com, bif-shp1")
    
class BiferShellIpHost(BiferShellType):
    def __init__(self):
        BiferShellType.__init__(self, "Hostname or IP Address. Ex: 192.168.10.200, www.google.com")
        self.ip_type = BiferShellIp()
        self.host_type = BiferShellHost()
    def validate_value(self, value):
        return self.ip_type.validate_value(value) or \
                self.host_type.validate_value(value)


class BiferShellWebUrl(BiferShellType):
    def __init__(self):
        BiferShellType.__init__(self, "Web URL, Ex: http://www.debian.org or https://www-nasa.gov")

    def validate_value(self, value):
        if value.startswith("http://") or value.startswith("https://"):
            return True
        else:
            return False

    def values(self, incomplete_word):
        if incomplete_word.startswith("http://") or incomplete_word.startswith("https://"):
            return []
        else:
            return ["http://", "https://"]
    
                
class BiferShellCidr(BiferShellType):
    def __init__(self): 
        BiferShellType.__init__(self,  
                                "Address in Classless Inter-Domain Routing  notation: Ex: 192.168.1.100/24")
    def validate_value(self, value):
        try:
            ip,bits = value.split('/')
            num_bits = int(bits)
            return True    
        except:
            return False
                
class BiferShellMac(BiferShellType):
    def __init__(self): 
        BiferShellType.__init__(self, "MAC or Ethernet Address in hex notation. Ex: 00:01:02:03:04:08")
    def validate_value(self, value):
        regexp = r"([0-9A-F][0-9A-F]:){5}([0-9A-F][0-9A-F])"
        match = re.match(regexp, value.upper())
        if match == None:
            return False
        else:
            return match.group().upper() == value.upper()


class BiferShellNet(BiferShellType): 
    def __init__(self): 
        BiferShellType.__init__(self)
    
class BiferShellNetMask(BiferShellType):
    def __init__(self): 
        BiferShellType.__init__(self, "Netmask in Dot-decimal Address. Ex: 255.255.255.0")

    def validate_value(self, value):
        return  bosip.Ip.validate_netmask(value)
    

class BiferShellNetIf(BiferShellType):
    def __init__(self): 
        BiferShellType.__init__(self, "Ethernet interface. Ex: eth0, eth1, eth0:0")
    def validate_value(self, value):
        return value in self.values('')
        
    def normalize(self, value):
        return value
    
    def values(self, incomplete_word):
        return ['eth0','eth0:0', 'eth1', 'eth1:0', 'eth2','eth2:0', 'br0']

class BiferShellInt(BiferShellType):
    def __init__(self): 
        BiferShellType.__init__(self, "Integer value. Ex: 42")
    def validate_value(self, value):
        try:
            int(value)
            return True
        except:
            return False
        
class BiferShellFloat(BiferShellType):
    def __init__(self): 
        BiferShellType.__init__(self, "Decimal number")
    def validate_value(self, value):
        try:
            float(value)
            return True
        except:
            return False


class BiferShellBool(BiferShellType):
    def __init__(self): 
        BiferShellType.__init__(self, "Coditional value. Accepted values 'true', 'false', '1', '0'")
    def validate_value(self, value):
        return value in self.values('')
        
    def normalize(self, value):
        return value
    
    def values(self, incomplete_word):
        return ['true', 'false', '1', '0']

class BiferShellState(BiferShellType):
    def __init__(self): 
        BiferShellType.__init__(self, "State value. Accepted values 'on', 'off', 'up', 'down'")
    def validate_value(self, value):
        return value in self.values('')
        
    def normalize(self, value):
        return value
    
    def values(self, incomplete_word):
        return ['on', 'off', 'up', 'down']
    
class BiferShellFile(BiferShellType):
    def __init__(self): 
        BiferShellType.__init__(self, "Filename with absolute path")
    def validate_value(self, Value):
        # TODO: Implement
        return True
        
    def normalize(self, value):
        return value

    def files(self, incomplete_path):
        return  [f for f in glob.glob(incomplete_path + '*') if f[-1:] not in ['~', '#']]
    
    def values(self, incomplete_word):
        paths = []
        for f in self.files(incomplete_word):
            if os.path.isdir(f):
                paths.append(f + '/')
            else:
                paths.append(f)

        if len(paths) == 1 and os.path.isdir(paths[0]):
            return self.values(paths[0])
        return paths
    

class BiferShellKernelVar(BiferShellType):
    def __init__(self):
        BiferShellType.__init__(self, "Kernel variable. Ex: net.unix.max_dgram_qlen or fs.mqueue.msgsize_max")
        self.kernel_vars=[]
        for line in os.popen("sysctl -A 2>/dev/null").readlines():
            self.kernel_vars.append(line.split('=')[0].strip())
    
    def values(self, incomplete_word):
        return self.kernel_vars
    
class BiferShellCmd(BiferShellType):
    def __init__(self): 
        BiferShellType.__init__(self, "Cli available functions")
        
    def values(self, incomplete_word):
        if self.cli == None:
            return []
        else:
            functions = self.cli.get_functions()
            cmds = sorted(list(set([a.split('_')[1] for a in functions])))
            return cmds


 
 
class BiferShellHexNumber(BiferShellType):
    def __init__(self): 
        BiferShellType.__init__(self, "Hex number value. Ex: FF02FE3A")
    def validate_value(self, value):
        try:
            int(value, 16)
            return True
        except:
            return False
 
