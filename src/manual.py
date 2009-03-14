#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Alea-Soluciones (Bifer) 2007, 2008, 2009
# Licensed under GPL v3 or later, see COPYING for the whole text

'''
  $Id:$
  $URL:$
  Alea-Soluciones (Bifer) (c) 2007
  Created: eferro - 1/11/2007

'''



try:
    import xml.etree.ElementTree as ET
except:
    import elementtree.ElementTree as ET
    
import boscliutils
import boscli

def generate_types_doc(node):
    ET.SubElement(node,"h1").text = "Type System"
    ET.SubElement(node,"p").text = "\n"


def generate_introduction(node):
    ET.SubElement(node,"h1").text = "Introduction"
    ET.SubElement(node,"p").text = """
BCLI. Bifer (operating system) Command Line Interface.\n
    """
    ET.SubElement(node,"p").text = """\n
    """
def generate_function_doc(node, f):
    priv,mode = boscli.get_cli().get_function_info(f)
    f_name = ' '.join(f.split('_')[1:])
    
    ET.SubElement(node,"em").text = f_name + (' (priv %d, mode %s)' % (priv,mode)) + '\n'
    ET.SubElement(node,"br")

    text = boscli.get_function_help(f.split('_')[1:])
        
    help_lines = text.split('\n')
    short_help = help_lines[0]
    help_node = ET.SubElement(node,"p")
    help_node.text = short_help + '\n'
    if len(help_lines) > 1:
        extended_help = ''.join(text.split('\n')[1:])
        ET.SubElement(help_node,"br").text = extended_help + '\n'
    pass

def generate_doc(node):
    tittle = ("Functions").capitalize()
    ET.SubElement(node,"h2").text = tittle
    ET.SubElement(node,"p").text = """
    
    """
    ET.SubElement(node,"h3").text = "Commands"
    
    cmd = None
    for f in sorted(boscli.get_cli().get_functions()):
        cmd_name = f.split('_')[1]
        if cmd_name != cmd:
            ET.SubElement(node,"b").text = cmd_name + '\n'
            ET.SubElement(node,"br")
            ET.SubElement(node,"br")
            cmd = cmd_name
 
        generate_function_doc(node, f)
            
        
def generate_html_user_doc():
    root = ET.Element("html")
    head = ET.SubElement(root, "head")
    title = ET.SubElement(head, "title")
    title.text = 'BCLI User Manual'
    body = ET.SubElement(root, "body")
    
    generate_introduction(body)
    generate_types_doc(body)
    ET.SubElement(body,"h1").text = "Commands Reference"
    
    generate_doc(body)
    
    # wrap it in an ElementTree instance, and save as XML
    tree = ET.ElementTree(root)
    tree.write("bcli_user_manual.html")
