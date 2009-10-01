#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Alea-Soluciones (Bifer) 2007, 2008, 2009
# Licensed under GPL v3 or later, see COPYING for the whole text

'''
  $Id:$
  $URL:$
  Alea-Soluciones (Bifer) (c) 2009
  Created: eferro - 20/9/2009
'''



import boscliutils
import bostypes


def context_pop():
    print "context_pop"
    get_cli().pop_context()
    get_cli().set_prompt()
    dynamic_pop_funct = 'dynbcli_%s_exit' % get_cli().context().replace(" ", "_")
    print "Removed '%s'" % dynamic_pop_funct
    get_cli().add_function(dynamic_pop_funct)

def bcli_context_show():
    print get_cli().context()

def bcli_context_push_STRING(context):
    print "pushing %s" % context
    get_cli().push_context(context)

def bcli_context_pop():
    print "pop"
    get_cli().pop_context()
    get_cli().set_prompt()


def bcli_net_configure_STRING(interface):
    print "pushing %s" % interface
    get_cli().push_context('net configure %s' % interface)

def bcli_net_configure_STRING_set_ip(interface):
    print "bcli_net_configure_STRING_set_ip(interface)"

def bcli_net_configure_STRING_set_default_gw(interface):
    print "bcli_net_configure_STRING_set_default_gw(interface):"


