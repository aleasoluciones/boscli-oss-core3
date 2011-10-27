#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Alea-Soluciones (Bifer) 2007, 2008, 2009
# Licensed under GPL v3 or later, see COPYING for the whole text

import boscli


def get_function_name(function):
    '''Return the real simbol name of a function from the function sintax in the bcli internal format'''
    return 'bcli_' + ('_'.join(function))

def get_function_help(function):
    '''Return all the doc of a function.
If the function have no doc, it returns "Not documented yet"
'''
    f = boscli.get_cli().get_function(function)
    doc = f.__doc__
    if doc == None:
        doc = "Not documented yet\n"
    return doc    
