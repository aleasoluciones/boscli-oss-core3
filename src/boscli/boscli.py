#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Alea-Soluciones (Bifer) 2007, 2008, 2009
# Licensed under GPL v3 or later, see COPYING for the whole text

'''
  $Id:$
  $URL:$
  Alea-Soluciones (Bifer) (c) 2007
  Created: eferro - 7/7/2007
'''


import readline
import posixpath
import os, signal
import os.path
import sys, getpass
import getopt
import atexit
from . import bostypes
from . import boscliutils
from . import privileges
import string
import configparser
import glob
import imp
import inspect
from .helpers import *


# Wraper to access to the unique instance of BiferShell
def get_cli():
    return BiferShell.get_instance()




class BiferShell:

    instance = None

    @staticmethod
    def get_instance():
        return BiferShell.instance

    def __init__(self,
                 name,
                 confpath,
                 nopasswd_superuser,
                 extensions,
                 debug=False):

        if BiferShell.instance != None:
            raise RuntimeError("BiferShell is a Singleton. So is ilegal to try to instanciate twice")
        # register singleton instance
        BiferShell.instance = self

        self.__debug = debug
        self.__name = name
        self.__confpath = confpath
        refusedfunctions = []
        if self.__confpath != None:
            boscliutils.Log.info("Parsing '%s' conf file" % self.__confpath)
            config = configparser.configparser()
            res = config.read(os.path.expanduser(self.__confpath))
            if len(res) == 0:
                boscliutils.Log.warning("Error parsing '%s' conf file" % self.__confpath)
                raise ValueError("Error parsing '%s' conf file" % self.__confpath)

            boscliutils.Log.info("'%s' conf file parsed" % self.__confpath)
            if config.has_section('refusedfunctions'):
                refusedfunctions = [kv[1] for kv in config.items('refusedfunctions')]


        if not sys.stdin.isatty(): # redirected from file or pipe
            self.__interactive = False
        else:
            self.__interactive = True

        self.__cliFunctionsManager = privileges.CliFunctionsManager(self.__name, refusedfunctions)
        self.__cliFunctionsManager.init_privileges()

        self.nopasswd_superuser = nopasswd_superuser
        self.type_manager = bostypes.BiferShellTypeManager()
        self.type_manager.set_cli(self)
        self.init_readline()
        self.init_history()
        self.completekey = 'tab'
        self.host = os.popen('hostname').read().strip()
        self.extensions = extensions
        self.__pager = False
        self.__exit_functs = []

        self.init_commands()
        self.clear_filter()
        self.in_command_execution = False

    def push_context(self, context):
        self.__cliFunctionsManager.push_context(context)
        self.set_prompt()
        dynamic_pop_funct = 'dynbcli_%s_exit' % get_cli().context().replace(" ", "_")
        self.add_function(dynamic_pop_funct, self.context_pop)

    def context_pop(self):
        """Exit from current mode"""
        dynamic_pop_funct = 'dynbcli_%s_exit' % get_cli().context().replace(" ", "_")
        self.remove_function(dynamic_pop_funct)
        self.pop_context()
        self.set_prompt()


    def context(self):
        return self.__cliFunctionsManager.context()


    def pop_context(self):
        self.__cliFunctionsManager.pop_context()


    def register_exit_funct(self, func):
         self.__exit_functs.append(func)

    def executing_command(self):
        return self.in_command_execution

    def init_commands(self):
        self.functions_files = {}
        self.functions_sintax = []
        self.alias = {}
        self.set_prompt()

        # First we import commands defined in this file
        self.import_cmds()
        self.load_extensions()

        # Check for problems for symbols loaded
        self.__cliFunctionsManager.validate_conf()


    def add_type(self, type_name, type_class_instance):
        self.type_manager.add_type(type_name, type_class_instance)

    def get_type(self, type_name):
        return self.type_manager.get_type(type_name)

    def get_type_names(self):
        return self.type_manager.get_types()


    def get_nopasswd_superuser(self):
        return self.nopasswd_superuser

    def change_mode(self, mode):
        self.__cliFunctionsManager.change_mode(mode)
        self.set_prompt()

    def change_priv(self, priv):
        self.__cliFunctionsManager.change_priv(priv)
        self.set_prompt()

    def change_priv_passwd(self, priv):
        self.__cliFunctionsManager.change_priv_passwd(priv)

    def change_mode_passwd(self, mode):
        self.__cliFunctionsManager.change_mode_passwd(mode)


    def set_privilege(self, min_privileges, mode, function_name):
        self.__cliFunctionsManager.set_function_privileges(min_privileges, mode, function_name)

    def change_initial_privilege(self, privilege):
        self.__cliFunctionsManager.change_initial_privilege(privilege)

    def get_mode(self):
        return self.__cliFunctionsManager.get_mode()

    def get_active_functions(self):
        return self.__cliFunctionsManager.get_active_functions()

    def get_functions(self):
        return self.__cliFunctionsManager.get_functions()

    def get_function_info(self, function):
        return self.__cliFunctionsManager.get_function_info(function)

    def get_extension_paths(self):
        return self.extensions

    def load_extensions(self):
        for ext in self.extensions:
            if not os.path.isdir(ext):
                boscliutils.Log.error("'%s' is not a extension dir" % ext, None)
            boscliutils.Log.debug("'%s' ext dir loading" % ext)
            for entry in glob.glob(os.path.join(ext, "*.py")):
                try:
                    self.import_cmds_file(entry)
                    boscliutils.Log.debug("'%s' imported" % entry)
                except IOError as ex:
                    boscliutils.Log.warning("Can access to '%s' extension file" % entry)
                except Exception as ex:
                    module_str = "Module '%s' import error" % os.path.basename(entry.strip())[:-3]
                    boscliutils.Log.error(module_str, ex)

    def init_readline(self):
        init_file = os.path.expanduser("~/.%s-init" % self.__name)
        readline.parse_and_bind("set bell-style visible")
        try:
            readline.read_init_file(init_file)
        except IOError:
            pass

    def init_history(self):
        histfile=os.path.expanduser("~/.%s-history" % self.__name)
        try:
            readline.read_history_file(histfile)
        except IOError:
            pass
        atexit.register(self.save_history, histfile)

    def save_history(self, histfile):
        readline.write_history_file(histfile)

    ## Function to work with aliases ----------------------
    def add_alias(self, alias_name, text):
        self.alias[alias_name] = text
    def remove_alias(self, alias_name):
        try:
            del self.alias[alias_name]
        except KeyError:
            pass
    def alias_value(self, alias_name):
        return self.alias[alias_name]
    def expand_alias(self, text):
        for alias_name in self.alias.keys():
            text = text.replace(alias_name, self.alias[alias_name])
        return text
    def get_alias(self):
        return self.alias
    ##------------------------------------------------------

    def expand_abbrevs_filter(self, filter_text):
        expanded_filter = filter_text
        try:
            filter_cmd = filter_text.split()[0]
            match = self.word_complete(filter_cmd, ['include', 'exclude', 'begin'])[0]
            expanded_filter = expanded_filter.replace(filter_cmd, match)
        except IndexError:
            pass

        return expanded_filter

    def expand_abbrevs(self, text):
        expanded_text = ''
        prev_words = []
        for word in text.split():
            # we try to complete
            completions = self.complete_word(prev_words, word)
            if len(completions) == 1:
                # If there is only one completion we select this one
                # as the abbrev expansion
                expanded_text = expanded_text + ' ' + completions[0]
                prev_words.append(completions[0])
            else:
                # We don't have a unique completion (or none at all)
                # so we let the word without changes
                expanded_text = expanded_text + ' ' + word
                prev_words.append(word)
        return expanded_text

    def prompt_str(self):
        context_info = self.__cliFunctionsManager.context_info()
        return '(%s) %s %s ' % (self.host, self.__name, context_info)

    def set_prompt(self):
        """Change the prompt using the host and the mode"""
        if self.__interactive:
            self.prompt = self.prompt_str()
        else:
            self.prompt = ''

    def pre_input_hook(self):
        if self.lastcommandhelp:
            readline.insert_text(self.lastline)
            readline.redisplay()
            self.lastcommandhelp = False

    def cmdloop(self, intro=None):
        self.old_completer = readline.get_completer()
        self.old_completer_delims = readline.get_completer_delims()
        readline.set_completer(self.complete)
        readline.parse_and_bind(self.completekey+": complete")
        readline.parse_and_bind("set bell-style none")
        readline.parse_and_bind("set show-all-if-ambiguous")
        readline.parse_and_bind("set completion-query-items -1")

        # If press help key, add the character and accept the line
        readline.parse_and_bind('"?": "\C-q?\C-j"')
        # Register a function for execute before read user
        # input. We can use it for insert text at command line
        readline.set_pre_input_hook(self.pre_input_hook)
        readline.set_completer_delims(' \t\n')

        try:
            stop = None
            while not stop:
                try:
                    line = input(self.prompt)
                except EOFError:
                    line = 'EOF'

                stop = self.onecmd(line)
                stop = self.postcmd(stop, line)
        finally:
            readline.set_completer(self.old_completer)
            readline.set_completer_delims(self.old_completer_delims)


    def select_execute(self, line):
        """Select the function to execute and return True if we execute the function
        and false, if we can't find a function to execute or there is more than one
        function to execute"""

        filter = None
        if '|' in line:
            parts = line.split('|')
            cmd = parts[0].strip()
            filter = parts[1:][0].strip()
            filter = self.expand_abbrevs_filter(filter)
        else:
            cmd = line
        cmd = self.expand_alias(cmd)
        cmd = self.expand_abbrevs(cmd)

        function_matches = self.__select_functions_that_matches(cmd)
        same_len_functions = [function for function in function_matches if len(function) == len(cmd.split())]
        if len(same_len_functions) == 1:
            self.execute(same_len_functions[0], cmd, filter)
            return True
        exact_match = [function for function in same_len_functions if function == cmd.split()]
        if exact_match:
            self.execute(exact_match[0], cmd, filter)
            return True
        else:
            return function_matches

    def __select_functions_that_matches(self, cmd):
        words = cmd.split()
        match_list = []
        for function in self.get_active_functions():
            if self.match(function, words) == True:
                match_list.append(function)

        match_list = sorted(match_list, key=len)
        return match_list

    # FIXME: Change implementation for not use global info for filters
    def get_filter(self):
        return self.__filter
    def clear_filter(self):
        self.__filter = None

    def pager_on(self):
        self.__pager = True
    def pager_off(self):
        self.__pager = False
    def pager(self):
        return self.__pager

    def execute(self, function, line, filter):
        """Execute function with the concret info in line
        """
        self.in_command_execution = True
        try:
            boscliutils.Log.debug("CLI Cmd: '%s'" % line.strip())
            # FIXME: Change implementation for not use global info for filters

            out = sys.stdout

            cmd = None
            regexp = None

            if filter != None:
                if boscliutils.validate_filter(filter):
                    self.__filter = filter
                    (cmd, regexp) = filter.split()
                else:
                    return

            # The output allways is conected with the filter
            sys.stdout = boscliutils.FilterOut(out, regexp, cmd, self.pager())

            try:
                args = line.split()
                self.__cliFunctionsManager.execute(function, args)
            except ValueError as ex:
                print("Can't be processed. ", ex)
            except Exception as ex:
                print("CLI Cmd execution failed: '%s'" % line)
                boscliutils.Log.debug("CLI Cmd execution failed: '%s'" % line)
                if self.__debug:
                    import traceback
                    traceback.print_exc(file=sys.stderr)

            if filter != None:
                self.clear_filter()

            sys.stdout = out

            boscliutils.Log.debug("CLI Cmd end: '%s'" % line.strip())
        except IndexError as e:
            boscliutils.Log.error("Error executing CLI Cmd: '%s'" % line.strip())
            boscliutils.Log.error("Exception: %s" % e)
            print(e)
        finally:
            self.in_command_execution = False

    def normalize_line(self, line):
        """Return the user line but with modifications forn context and show on.
        If we have context, the line returned included the corresponding text
        for the initial line and the context
        If we have a context, the '*' as the first caracter of the line indicate that
        that line don't use the context, so in that case whe only return the line
        whitout this initial character
        """

        if len(line)>0 and line[0] == '*':
            return line[1:]
        return (self.context() + " " + line)

    def onecmd(self, line):
        if line == 'EOF':
            self.quit()
        elif line == "" or line.startswith('!'):
            pass
        elif line[-1] == '?':
            self.show_help(line[:-1])
            self.lastcommandhelp = True
        else:
            try:
                line = self.normalize_line(line).strip()
                if line == '':
                    return None
                ret = self.select_execute(line)
                if ret == True:
                    return None
                else:
                    if len(ret) > 0:
                        self.default(line)
                        print
                        print("May be you are looking for: ")
                        self.interactive_help(line.split(), '')
                        return None
                # Si no la hemos podido ejecutar decimos que sintaxis desconocida
            except KeyError as ex:
                print(line)
                print(dir())
                print(globals())
                print("...")
            self.default(line)
        return None


    def postcmd(self, stop, line):
        return stop

    def default(self, line):
        if line != None:
            print("Syntax Error. Unknow command '%s'" % (line))
            boscliutils.Log.debug( "Syntax Error. Unknow command '%s'" % (line))

        return False

    ## Some helper functions
    def word_complete(self, text, words):
        return [a for a in words if a.startswith(text)]


    def exec_cmds_file(self, command_file):
        """Execute the command in the file, except exit/EOF command"""
        print("executing %s" % command_file)
        if os.path.isfile(command_file):
            for line in open(command_file).readlines():
                line = line[:-1]
                if len(line):
                    stop = self.onecmd(line)
                    stop = self.postcmd(stop, line)
            print("finish executing %s" % command_file)
            print
        else:
            raise RuntimeError('%s is not a valid file' % command_file)
        pass

    def add_function(self, symbol_name, symbol):
        if symbol_name.find('_') == -1 or not symbol_name.split('_')[0] in ['bcli', 'dynbcli']:
            raise ValueError("'%s' is not a valid boscli func name" % symbol_name)
        self.functions_sintax.append(symbol_name.split('_')[1:])
        self.__cliFunctionsManager.append(symbol_name, symbol)


    def remove_function(self, symbol_name):
        self.functions_sintax.remove(symbol_name.split('_')[1:])
        self.__cliFunctionsManager.remove(symbol_name)


    def get_function(self, func_name):
        return self.__cliFunctionsManager.get_function(func_name)


    def import_cmds_file(self, path):
        module_name = os.path.splitext(os.path.basename(path))[0]
        new_module = imp.load_source(module_name,path)
        members = inspect.getmembers(new_module)
        for (name, value) in members:
            if inspect.isfunction(value) and name.startswith('bcli_'):
                self.functions_files[name] = path
                self.functions_sintax.append(name.split('_')[1:])
                self.__cliFunctionsManager.append(name, value)

    def import_cmds(self):
        # TODO: Refactor import_cmds_file
        # FIXME: Remove???
        for s in globals():
            if s.startswith('bcli_'):
                self.functions_files[s] = ''
                self.functions_sintax.append(s.split('_')[1:])
                self.__cliFunctionsManager.append(s, globals()[s])


    def run(self):
        """Read and execute commands until the user decide to finish"""
        try:
            self.cmdloop()
        except KeyboardInterrupt:
            print
            self.quit()

    def quit(self):
        boscliutils.Log.log("Exit boscli")

        # Execute extensions exit callbacks
        for f in self.__exit_functs:
            boscliutils.Log.info("Executing exit funct '%s'" % str(f))
            f()

        if self.__interactive:
            print
            print("bye")

        sys.exit(0)

    def get_normalize_func_name(self, f):
        func_name = get_function_name(f)
        word_list = func_name.split('_')[1:]
        final_word_list = []
        for w in word_list:
            if w.isupper(): final_word_list.append('<' + w + '>')
            else: final_word_list.append(w)
        f_name = ' '.join(final_word_list)
        return f_name

    def get_basic_help_str(self,f):
        f_name = self.get_normalize_func_name(f)
        f_help = get_function_help(f).split('\n')[0]


        # If we have a context defined we remove the
        # corresponding words of the context from the funct
        # name, so the help only show the rest of the funct name
        num_context_words = len(self.__cliFunctionsManager.context().split())
        f_name = " ".join(f_name.split()[num_context_words:]).strip()
        if f_name == '':
            return None
        return "'%s' => %s" % (f_name, f_help)

    def basic_help(self):
        self.interactive_help([], '')

    def interactive_help(self, prev_words, partial_word):
        basic_help = False
        if prev_words == [] and partial_word == '':
            # The user need high level help (basic_help)
            basic_help = True
        print
        help_lines = []
        for f in self.get_active_functions():
            if basic_help and len(f) > 1:
                continue
            if self.match(f, prev_words):
                try:
                    if f[len(prev_words)].startswith(partial_word):
                        help = self.get_basic_help_str(f)
                        if help != None:
                            help_lines.append(self.get_basic_help_str(f))
                except IndexError:
                    help = self.get_basic_help_str(f)
                    if help != None:
                        help_lines.append(self.get_basic_help_str(f))
        if len(help_lines) == 0:
            print("No help available")
        else:
            for line in sorted(help_lines):
                print(line)


    def show_help(self, line):
        """Generate help for line specified"""
        # Check for empty line, and for a space after the last word
        if line[-1:] == ' ' or line[-1:] == '':
            # We don't have incomplete_word
            previous_words = self.normalize_line(line).split()
            incomplete_word = ''
        else:
            previous_words = self.normalize_line(line).split()[:-1]
            incomplete_word = self.normalize_line(line).split()[-1:][0]

        self.interactive_help(previous_words, incomplete_word)
        # Save this line for restore it
        # and continue editing, after show help
        self.lastline = line



#-----------------------------------------
    def complete(self, word_to_complete, state):
        """Return the next possible completion for 'text'.

        This is called successively with state == 0, 1, 2, ... until it
        returns None.  The completion should begin with 'text'.

        """

        # TODO Refactor
        if state == 0:
            line = readline.get_line_buffer()
            origline = line
            try:
                word_at_point = None
                if line[readline.get_endidx()] == ' ':
                    word_at_point = word_to_complete
                else:
                    word_at_point = word_to_complete + line[readline.get_endidx():].split()[0]
            except Exception as ex:
                word_at_point = None

            if len(line) > readline.get_endidx():
                line = line[:readline.get_endidx()]

            if line.find('|') != -1:
                self.matches = None
                # FIXME: Check if we are at the right hand of the pipe
                filter_len = len(line.split('|')[1].split())
                if filter_len == 0 or (filter_len == 1 and word_to_complete != ''):
                    self.matches = self.word_complete(word_to_complete,
                                                      ['include',
                                                       'exclude',
                                                       'begin',
                                                       '|include',
                                                       '|exclude',
                                                       '|begin',
                                                       '| '])
                    if len(self.matches) == 1:
                        if word_at_point == self.matches[0]:
                            # Don't return the same word that already have at point
                            return None
                        return self.matches[0] + ' '
                    elif len(self.matches) > 1:
                        return self.matches[0]
                    else:
                        return None
            elif word_to_complete == '':
                # We are not completing a word
                # If the actual word is empty the previous are all
                # the words
                previous_words = self.normalize_line(line).split()
                self.matches = self.next_words(previous_words, '')
                return self.matches[0]

            elif word_to_complete.startswith('<'):
                # We don't complete type values....
                self.matches = None
            else:
                # there is a word to complete
                if word_to_complete[0]=='@':
                    self.matches = self.word_complete(word_to_complete, self.alias.keys())
                else:
                    # If the actual word is NOT empty the previous are all
                    # the words minus the actual word
                    previous_words = self.normalize_line(line).split()[:-1]
                    self.matches = self.complete_word(previous_words, word_to_complete)

                    if len(self.matches) == 1:
                        if word_at_point == self.matches[0]:
                            # Don't return the same word that already have at point
                            return None
                        return self.matches[0] + ' '
                    return self.matches[0]
        else: # state != 0. return the corresponding match or None
            try:
                match = self.matches[state]
                return match
            except IndexError:
                return None

    def redisplay(self):
        line = readline.get_line_buffer()
        print(self.prompt_str() + line.strip())



    def type_values(self, type_name):
        return self.type_manager.values(type_name, '')


    def validate_value(self, type_name, value):
        return self.type_manager.validate_value(type_name, value)

    def next_words(self, prev_words,  incomplete_word):

        num_words = len(prev_words)
        match_list = []
        # Validate
        for function in self.get_active_functions():
            if self.match(function, prev_words):
                # we have a match with prev_words
                try:
                    next_word = function[len(prev_words)]

                    if self.type_manager.is_type(next_word):
                        fixed_values = False
                        # If the next word represent a type we must add
                        # all the posible "completes" for this type
                        for value in self.type_manager.values(next_word, incomplete_word):
                            fixed_values = True
                            match_list.append(value)
                        # If we don't have a fixed number of completion
                        # we include a type representation to show the user
                        # that this type can be a valid completion
                        if not fixed_values:
                            match_list.append('<' + next_word + '>')
                    else:
                        match_list.append(next_word)
                except IndexError as ex:
                    pass
        return match_list

    def match(self, function, prev_words):
        """Return True if the function match all the prev_words"""
        if len(prev_words) == 0:
            # Of thre is no previous words allways match :)
            return True
        if len(function) >= len(prev_words):
            for pos in range(0, len(prev_words)):
                if function[pos].startswith(prev_words[pos]):
                    # accept abbreviations of the function word
                    # See #61

                    # Ok. lets continue
                    continue
                elif self.type_manager.is_type(function[pos]) and \
                    self.validate_value(function[pos], prev_words[pos]):
                    # Ok. lets continue
                    continue
                else:
                    # It's not the same word and it not match the correct type
                    # so not a good choice
                    return False
            # If we reach this point, we are lucky... it matchs!!!
            return True
        else:
            # Function is more short than prev_words so a match is not possible
            return None


    def complete_word(self, prev_words, incomplete_word):
        # find the next words
        res = self.next_words(prev_words, incomplete_word)
        # only accepts words that starts with the imcomplete_word
        res = [a for a in res if a.startswith(incomplete_word)]
        # Eliminate duplicated
        return list(set(res))

    def confirm(self, prompt):
        result = None
        prompt = prompt + " (Y/[N]): "
        while True:
            print(prompt)
            result = boscliutils.get_ch()
            if result.upper() in ['Y', 'N']:
                return  result.upper() == 'Y'
            elif result == '\r':
                return False


def usage():
    usage_msg = """
Use mode: boscli [OPTIONS] [extdir1 extdir2 ...]
Open a interactive Command Line Interface/Interpreter

The valid options are:
(The mandatory argument for "long format" options are also
mandatory for the correspondent short option)

  -h, --help
      show this help
  -a, --name
      boscli instance name. Used for separate conf/history files,
      and to identify log messages.
  -c, --conf = path
      load the specified file as configuration. The configuration
      file is used basically to deactivate already defined boscli
      functions
  -n, --nopasswd
      don't ask for the password when change to a "mode" if we are root.
  -f, --file = path
      read and execute the commands in this file before enter
      in interactive mode.
  -v, --verbose
      log more info to system log
  -d, --debug
      log debug messages to system log

More info at Boscli hompage
http://oss.alea-soluciones.com/trac/wiki/BoscliOss
"""
    print(usage_msg)


def initial_error(err_msg):
    print("Error.")
    print(err_msg)
    print("Use: boscli -h to see the how to use the command")
    sys.exit()


def handler(signum, frame):
    cli = get_cli()
    if cli != None:
        if cli.executing_command() == True:
            return
        try:
            bcli_exit()
        except NameError:
            # If there is no a bcli_exit function
            # defined, end execution
            # The core lib include a bcli_exit at restrictedmodes.py
            sys.exit()

        get_cli().redisplay()
        readline.redisplay()
    else:
        sys.exit()



def main():
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTSTP, handler)


    try:
        opts, args = getopt.getopt(sys.argv[1:], \
                                   "vdnhf:a:c:i", \
                                   ["vervose","debug", "nopasswd", "help",
                                    "file=", "name", "conf", "interactive"])
    except getopt.GetoptError as err:
        # print help information and exit:
        print(str(err)) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    command_file = None
    nopasswd_superuser = False
    verbose = False
    debug = False
    name = 'boscli-oss'
    confpath = None
    interactive = True
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-v", "--verbose"):
            verbose = True
        elif opt in ("-a", "--name"):
            name = arg
        elif opt in ("-c", "--conf"):
            confpath = arg
        elif opt in ("-d", "--debug-level"):
            debug = True
        elif opt in ("-n", "--nopasswd"):
            nopasswd_superuser = True
        elif opt in ("-f", "--file"):
            command_file = os.path.normpath(arg)
        elif opt in ("-i", "--interactive"):
            # ignore this option
            # allways considerred interactive
            pass
        else:
            initial_error ("%s, unhandled option" % opt)



    boscliutils.Log.init(name, verbose, debug)
    boscliutils.Log.log("Starting %s" % name)


    # Open new CLI in normal mode
    cli = BiferShell(name, confpath, nopasswd_superuser, args, debug)
    if command_file: cli.exec_cmds_file(command_file)

    boscliutils.Log.info("Entering in interactive mode")
    cli.run()
    boscliutils.Log.info("End %s" % name)
