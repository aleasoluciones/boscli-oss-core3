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
import pickle
import os.path
import os
import time
import socket
import re

NONE, ENABLE, MANUF = 0,1,2
NORMAL, CONFIGURE = 'normal', 'configure'



class InvalidPassword(Exception):
    """Invalid password"""
    pass

class Privileges:
    def __init__(self, min_privileges, mode):
        self.__min_privileges = min_privileges
        self.__mode = mode

class CliFunctionsManager:
    def __init__(self, name, refusedfunctions):
        self.__name = name
        self.__refusedfunctions = refusedfunctions
        self.__prompts = {
            0: '>',
            1: '#',
            2: '*'
            }
        self.__priv_names = {
            0: '',
            1: 'enable',
            2: 'manuf'
            }
        self.__pass_file = "~/.%s_passwd" %  self.__name
        self.__privileges_file = "~/.%s_privileges"  %  self.__name
        self.__priv = 0
        self.__mode = 'normal'
        self.__valid_modes = ['normal', 'configure']

        self.__passwords = {}
        # try to read password file (if exists)
        try:
            file = open(self.__get_passfile_name(), "rb")
            self.__passwords = pickle.load(file)
        except IOError, ex:
            # If we can't read the file ignore it....
            pass
        self.__functions_access = {}
        self.__functions = {}
        

    def init_privileges(self):
        # try to read password file (if exists)
        try:
            file = open(self.__get_privilegesfile_name(), "rb")
            self.__priv = pickle.load(file)
        except IOError, ex:
            # If we can't read the file ignore it....
            pass

    def validate_conf(self):
        errors = [f for f in self.__functions_access.keys() if f not in self.__functions.keys()]
        for e in errors:
            boscliutils.Log.info("Access defined for an inexistent symbol: %s" % e)
            del self.__functions_access[e]


    def execute(self, function, args):
        str_function = '_'.join(function)
        f = self.__functions[str_function]
        f(args)

    def get_function(self, func_name):
        str_function = '_'.join(func_name)
        return self.__functions[str_function]

    def validate(self, function):
        try:
            min_priv, mode = self.__functions_access[function]

            # We cosider that a function is accesible if:
            # - We have a privilege level equal or grater
            #   than min priv level of funct
            # - We have configure mode (acces to normal and
            #   configure functs) or we have normal mode and
            #   the funct is defined for normal mode
            if  self.__priv >= min_priv and \
                    (self.__mode == CONFIGURE or self.__mode == mode):
                return True
        except KeyError:
            return False
        return False

    def valid_function(self, function_name):
        
        # At this moment, we only validate if the function
        # is configured to be refused ([refusedfunctions] section
        # at conf file
        for expr in self.__refusedfunctions:
            # The reg expr, can have spaces as word separator, so
            # we remove spaces at the begining and at the end, and
            # replace the internal separators with '_' that is the
            # real separator for functs names
            expr = expr.strip()
            expr = "_".join(expr.split())

            if expr != '' and re.match(expr, function_name):
                boscliutils.Log.debug("'%s' refused function (conf '%s')" % (function_name, expr))
                return False
        return True


    def append(self, function_name, func):        
        # Remove initial word, from functionname (bcli, dynbcli, etc)
        function_name = '_'.join(function_name.split('_')[1:])

        if not self.valid_function(function_name):
            boscliutils.Log.debug("'%s' refused function" % (function_name))
            return

        self.__functions[function_name] = func
        if not self.__functions_access.has_key(function_name):
            self.__functions_access[function_name] = [NONE, NORMAL]
    
    def remove(self, function_name):        
        # Remove initial word, from functionname (bcli, dynbcli, etc)
        function_name = '_'.join(function_name.split('_')[1:])
        del self.__functions[function_name]
        del self.__functions_access[function_name]

    def set_function_privileges(self,  min_priv, mode, function):
        # Remove initial word, from functionname (bcli, dynbcli, etc)
        function = '_'.join(function.split('_')[1:])
        self.__functions_access[function] = [min_priv, mode]
        
    def set_privileges(self, priv):
        self.__priv = priv
        return True
    
    def get_privileges(self): return self.__priv
    def set_mode(self, mode):
        self.__mode = mode
        return True
    def get_mode(self): return self.__mode

    def get_functions(self):
        funct = self.__functions_access.keys()
        funct.sort()
        return funct

    def get_function_info(self, function):
        return self.__functions_access[function]

    def get_active_functions(self):
        funct = []
        for f in self.__functions_access.keys():
            if self.validate(f): funct.append(f.split('_'))
        funct.sort()
        return funct

    def context_info(self):
        return "%d [%s] %s%s" % (self.__priv, 
                                 self.__priv_names[self.__priv],
                                 self.__mode,
                                 self.__prompts[self.__priv])


    def change_priv(self, priv):
        self.__change_priv(priv)

    def change_mode(self, mode):
        self.__change_mode(mode)
        

    def change_priv_passwd(self, priv):
        try:
            self.__passwords[priv] = self.__get_new_password()
            self.__dump_passwords();
            print 'Password set'
        except InvalidPassword, e:
            print "Error: ", e

    def change_mode_passwd(self, mode):
        try:
            self.__passwords[mode] = self.__get_new_password()
            self.__dump_passwords();
            print 'Password set'
        except InvalidPassword, e:
            print "Error: ", e

    def __change_mode(self, dest_mode):
        # FIXME refactor __change_priv and __change_mode
        try:
            if dest_mode == NORMAL:
                self.set_mode(dest_mode)
                return
            if self.__get_actual_password(dest_mode) == None:
                print 'No password defined for mode %s' % dest_mode
                try:
                    self.__passwords[dest_mode] = self.__get_new_password()
                    self.__dump_passwords();
                    print 'Password set'
                    print "Changed to %s..." % dest_mode
                    self.set_mode(dest_mode)
                    return
                except InvalidPassword, e:
                    print "Error: ", e
                    return
            else:
                if self.__passwords[dest_mode] == '':
                    print "Changed to %s..." % dest_mode
                    self.set_mode(dest_mode)
                else:
                    passwd = self.__get_password()
                    if passwd ==  self.__passwords[dest_mode] or passwd in self.__get_temp_passwords():
                        print "Changed to %s..." % dest_mode
                        self.set_mode(dest_mode)
                    else:
                        print "Invalid password"
        except:
            print "Invalid password"
        
    def __change_priv(self, dest_priv):
        # FIXME refactor __change_priv and __change_mode
        try:
            if dest_priv == 0:
                self.set_privileges(dest_priv)
                return
            if self.__get_actual_password(dest_priv) == None:
                print 'No password defined for privilege level %s' % dest_priv
                try:
                    self.__passwords[dest_priv] = self.__get_new_password()
                    self.__dump_passwords();
                    print 'Password set'
                    print "Changed to privilege level %s..." % dest_priv
                    self.set_privileges(dest_priv)
                    return
                except InvalidPassword, e:
                    print "Error: ", e
                    return
            else:
                if self.__passwords[dest_priv] == '':
                    print "Changed to privilege level %s..." % dest_priv
                    self.set_privileges(dest_priv)
                else:
                    passwd = self.__get_password()
                    if passwd ==  self.__passwords[dest_priv] or passwd in self.__get_temp_passwords():
                        print "Changed to privilege level %s..." % dest_priv
                        self.set_privileges(dest_priv)
                    else:
                        print "Invalid password"
        except:
            print "Invalid password"

    def __get_passfile_name(self):
        return  os.path.expanduser(self.__pass_file)
    def __get_privilegesfile_name(self):
        return  os.path.expanduser(self.__privileges_file)
    
    def __get_password(self):
        '''Prompt the user for the password and return it'''
        # We import the module only if we really need a password entry
        import getpass
        # FIX-ME
        # We can't use the prompt of the getpass because if we have a output
        # active the prompt appear after the user enter the password
        print "passwd: "
        return getpass.getpass('')

    def __get_new_password(self):
        '''Prompt the user for the password twice and return it if the 
        passwords match, throw exception if not.'''
        # We import the module only if we really need a password entry
        import getpass
        print "New password"
        passwd1 = self.__get_password()
        print "Repeat the password"
        passwd2 = self.__get_password()
        if passwd1==passwd2:
            return passwd1
        else:
            raise InvalidPassword("Introduced passwords don't match")

    def __dump_passwords(self):
        """Dump passwords to local file"""
        file = open(self.__get_passfile_name(), "wb")
        pickle.dump(self.__passwords, file)

    def change_initial_privilege(self, privilege):
        """Save initial privilege for this user"""
        file = open(self.__get_privilegesfile_name(), "wb")
        pickle.dump(privilege, file)


    def __get_actual_password(self, mode):
        try:
            return self.__passwords[mode]
        except KeyError:
            return None

    def __get_temp_passwords(self):
        """Dummie Algorithm for generate temporal passwords"""
        p = []
        seed1 = int(str(time.time()).split('.')[0])/10000
        seed2 = seed1 - 1
        seed3 = seed1 + 1
        host_seed = socket.gethostname()
        h_seed1 = str(ord(host_seed[0]))
        h_seed2 = str(ord(host_seed[1]))
        p.append(h_seed1 + str(seed1 % 1000) + h_seed2)
        p.append(h_seed1 + str(seed2 % 1000) + h_seed2)
        p.append(h_seed1 + str(seed3 % 1000) + h_seed2)
        return p

