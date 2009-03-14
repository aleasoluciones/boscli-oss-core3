#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Alea-Soluciones (Bifer) 2007, 2008, 2009
# Licensed under GPL v3 or later, see COPYING for the whole text

'''
  $Id:$
  $URL:$
  Alea-Soluciones (Bifer) (c) 2008
  Created: eferro - 24/09/2008
'''


import glob
import os.path
import boscliutils


get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_apache_disable_SITEENABLED')
get_cli().set_privilege(privileges.MANUF, privileges.NORMAL, 'bcli_apache_enable_SITEAVAILABLE')

class BiferShellSiteAvailable(bostypes.BiferShellType):
    def __init__(self): 
        bostypes.BiferShellType.__init__(self)
    def values(self, incomplete_word):
        sites = [os.path.basename(d) for d in glob.glob('/etc/apache2/sites-available/*')]
        return sites

class BiferShellSiteEnabled(bostypes.BiferShellType):
    def __init__(self): 
        bostypes.BiferShellType.__init__(self)
    def values(self, incomplete_word):
        sites = [os.path.basename(d) for d in glob.glob('/etc/apache2/sites-enabled/*')]
        return sites

get_cli().add_type('SITEENABLED', BiferShellSiteEnabled())
get_cli().add_type('SITEAVAILABLE', BiferShellSiteAvailable())



def bcli_apache_enable_SITEAVAILABLE(line_words):
    """Enable apache2 site (and reload conf)
    """
    site = line_words[2]
    print "Enabling apache2 site %s" % site    
    boscliutils.apache_enable_site(site)

def bcli_apache_disable_SITEENABLED(line_words):
    """Disable apache2 site (and reload conf)
    """
    site = line_words[2]
    print "Disabling apache2 site %s" % site
    boscliutils.apache_disable_site(site)




