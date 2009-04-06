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
import bostypes
import boscliutils
import privileges
import string

try:
    __default_base_path__ = os.environ['BOSCLI_LIB_PATH']
except KeyError:
    __default_base_path__ = 'lib/'



# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52304
# Helper class to create static methods (class methods)
class Callable:
    def __init__(self, anycallable):
        self.__call__ = anycallable


# Wraper to access to the unique instance of BiferShell
def get_cli():
    return BiferShell.get_instance()




class BiferShell:
    
    instance = None
    def get_instance():
        return BiferShell.instance
    get_instance = Callable(get_instance)
    
    mode_prompt = {
                   None:'>',
                   'enable':' (enable)#',
                   'configure':' (configure)#',
                   'manufacturer':' (manufacturer)#'
    }
    
    def __init__(self,
                 base_path,
                 init,
                 nopasswd_superuser,
                 test):         

        if BiferShell.instance != None:
            raise RuntimeError("BiferShell is a Singleton. So is ilegal to try to instanciate twice")
        # register singleton instance
        BiferShell.instance = self

        if not sys.stdin.isatty(): # redirected from file or pipe
            self.__interactive = False
        else:
            self.__interactive = True        

        self.__cliFunctionsManager = privileges.CliFunctionsManager()
        self.__cliFunctionsManager.init_privileges()

        self.nopasswd_superuser = nopasswd_superuser
        self.test = test
        self.type_manager = bostypes.BiferShellTypeManager()
        self.type_manager.set_cli(self)
        self.init_readline()
        self.init_history()
        self.base_path = base_path
        self.completekey = 'tab'
        self.host = os.popen('hostname').read().strip()
            
        if init: self.init_cli()
        self.init_commands()
        self.clear_filter()
        self.in_command_execution = False
        self.__pager = False



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

    def load_extensions(self):

        # We process all the python file from the base_path

        # FIXME don't use find / use python glob or similar
        for file_path in os.popen('find %s -name "*.py" -print 2>/dev/null' % self.base_path).readlines():
            try:
                if self.__interactive:
                    print "Importing %s" % file_path.strip()
                self.import_cmds_file(file_path.strip())
            except IOError, ex:
                # If the file is not readable there is no problem
                # because this is the only for control the commands
                # that we can use with this user
                pass
            except Exception, ex:
                print "Module '%s' import error" % os.path.basename(file_path.strip())[:-3]
                import traceback
                traceback.print_exc(file=sys.stdout)
 
        
            
    def init_readline(self):
        init_file = os.path.expanduser("~/.cli-init")
        readline.parse_and_bind("set bell-style visible")        
        try:
            readline.read_init_file(init_file)
        except IOError:
            pass
        
        
    def init_history(self):
        histfile=os.path.expanduser("~/.cli-history")
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
        
        
    def init_cli(self):
        """Display wellcome msg and init some CLI atributtes. Only use for root CLI"""
        self.version = '0.1'
        self.author = 'eferro'
        self.print_wellcome()
    
    def prompt_str(self):
        context_info = self.__cliFunctionsManager.context_info()
        return '(%s) bcli %s ' % (self.host, context_info)
        
    def set_prompt(self):
        """Change the prompt using the host and the mode"""
        if self.__interactive:
            self.prompt = self.prompt_str()
        else:
            self.prompt = ''
        
    def print_wellcome(self):
        """Display wellcome msg"""
        # Conf and Copyright info
        name = 'BiferCommandLineInterface (bcli)'
        init_msg = 'initializing %s ...' % name
        copyright = 'Copyright (c) 2007 Alea Soluciones'
        wellcome_msg = '''
Welcome to %(name)s %(ver)s
Interactive BiferOperatingSystem adminstration console.
%(copy)s %(author)s
        ''' % {'name':name, 'ver':self.version, 'copy':copyright, 'author':self.author}
        
        first_msg = """
For basic help:
Type h<ret> or help<help> for basic first level help.
Type ?<tab> at the end of a line to see the contextual help for this line 
        """
        print init_msg
        print wellcome_msg
        print first_msg

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
                    line = raw_input(self.prompt)        
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
            
        # First expand all the aliases
        cmd = self.expand_alias(cmd)
        # Second expand abbrevs
        cmd = self.expand_abbrevs(cmd)
        
        words = cmd.split()
        match_list = []

        similar_match_list = []
        
        # Validate 
        for function in self.get_active_functions():
            if self.match(function, words) == True and \
                len(words) == len(function):
                match_list.append(function)
            if self.match(function, words) == True and \
                len(words) != len(function):
                similar_match_list.append(function)
        if len(match_list) == 1:
            # Then Execute
            self.execute(match_list[0], cmd, filter)
            return True
        if len(match_list) > 1:
            print "Ambiguous command"
            return match_list
        else:
            return similar_match_list
    

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


    def validate(self, str):
        """Return str if only contains supported characters.
        In other cases, print a error msg and raise ValueError.
        The acepted characters are: letters, numbers and './-_:@'
        """
        allchars = string.maketrans('','')
        if not str.translate(allchars, './-_:@').isalnum():
            print "Error: Str '%s' contains invalid characters" % str
            raise ValueError("Str '%s' contains invalid characters" % str)
        return str


    def execute(self, function, line, filter):
        """Execute function with the concret info in line 
        """
        str_function = '_'.join(function)
        str_function = "_".join(('bcli', str_function))

        self.in_command_execution = True
        try:
            f = globals()[str_function]
            if self.test:
                print "(test) Cmd: '%s'" % (line)
            else:
                boscliutils.Log.info("CLI Cmd: '%s'" % line.strip())

                # FIXME: Change implementatio for not use global info for filters

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
                    f([self.validate(w) for w in line.split()])
                except ValueError:
                    print "Can't be processed."

                if filter != None:
                    self.clear_filter()

                sys.stdout = out

                boscliutils.Log.info("CLI Cmd end: '%s'" % line.strip())    
        except IndexError,e:
            boscliutils.Log.warning("Error executing CLI Cmd: '%s'" % line.strip())
            boscliutils.Log.debug("Exception: %s" % e)
            print e
        finally:
            self.in_command_execution = False
        
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
                line = line.strip()
                if line == '':
                    return None
                ret = self.select_execute(line)
                if ret == True:
                    return None
                else:
                    if len(ret) > 0:
                        self.default(line)
                        print
                        print "May be you are looking for: "
                        self.interactive_help(line.split(), '')
                        return None
                # Si no la hemos podido ejecutar decimos que sintaxis desconocida
            except KeyError, ex:
                print line
                print dir()
                print globals()
                print "..."
            self.default(line)
        return None

    
    def postcmd(self, stop, line):
        return stop
    
    def default(self, line):
        if line != None:
            print "Sintax Error. Unknow command '%s'" % (line)
        return False       
        
    ## Some helper functions
    def word_complete(self, text, words):
        return [a for a in words if a.startswith(text)]
    
    
    def exec_cmds_file(self, command_file):
        """Execute the command in the file, except exit/EOF command"""    
        print "executing %s" % command_file
        if os.path.isfile(command_file):
            for line in open(command_file).readlines():
                line = line[:-1]
                if len(line):
                    stop = self.onecmd(line)
                    stop = self.postcmd(stop, line)
            print "finish executing %s" % command_file
            print
        else:
            raise RuntimeError('%s is not a valid file' % command_file)
        pass
    
    def import_cmds_file(self, path):
        # TODO: Refactor import_cmds 
        act_symbols = globals().keys()
        execfile(path, globals(), globals())
        for s in globals().keys():
            if s not in act_symbols and  str(s).startswith('bcli_'):
                self.functions_files[s] = path
                self.functions_sintax.append(s.split('_')[1:])
                self.__cliFunctionsManager.append(s)
        

    def import_cmds(self):
        # TODO: Refactor import_cmds_file
        for s in globals():
            if s.startswith('bcli_'):
                self.functions_files[s] = ''
                self.functions_sintax.append(s.split('_')[1:])
                self.__cliFunctionsManager.append(s)

        
    def run(self):
        """Read and execute commands until the user decide to finish"""
        try:
            self.cmdloop()
        except KeyboardInterrupt:
            print
            self.quit()
            
    def quit(self):
        boscliutils.Log.info("Exit boscli")
        if self.__interactive:
            print
            print "bye"
        sys.exit(0)
    
    def get_normalize_func_name(self, f):
        word_list = get_function_name(f).replace('bcli_','').split('_')
        final_word_list = []
        for w in word_list:
            if w.isupper(): final_word_list.append('<' + w + '>')
            else: final_word_list.append(w)
        f_name = ' '.join(final_word_list)
        return f_name

    def get_basic_help_str(self,f):
        f_name = self.get_normalize_func_name(f)
        f_help = get_function_help(f).split('\n')[0]
        return "%s => %s" % (f_name, f_help)
            
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
                        help_lines.append(self.get_basic_help_str(f))
                except IndexError:
                    help_lines.append(self.get_basic_help_str(f))
        if len(help_lines) == 0:
            print "No help available"
        else:
            for line in sorted(help_lines):
                print line


    def show_help(self, line):
        """Generate help for line specified"""
        # Check for empty line, and for a space after the last word
        if line[-1:] == ' ' or line[-1:] == '':
            # We don't have incomplete_word
            previous_words = line.split()
            incomplete_word = ''
        else:
            previous_words = line.split()[:-1]
            incomplete_word = line.split()[-1:][0]            

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
            except Exception, ex:
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
                previous_words = line.split()
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
                    previous_words = line.split()[:-1]
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
        print self.prompt_str() + line.strip(),
        
        
 
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
                except IndexError,ex:
                    pass
        return match_list
    
    def match(self, function, prev_words):
        """Return True if the function match all the prev_words"""
    
        if len(prev_words) == 0:
            # Of thre is no previous words allways match :)
            return True
        if len(function) >= len(prev_words):
            for pos in range(0, len(prev_words)):
                if function[pos] == prev_words[pos]:
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
            print prompt
            result = boscliutils.get_ch()
            if result.upper() in ['Y', 'N']:
                return  result.upper() == 'Y'
            elif result == '\r':
                return False

    
def usage():
    usage_msg = """
Use mode: cli [OPTIONS]...
Open a interfactive Command Line Interface/Interpreter for 
BiferOperatimSystem. 

The valid options are:
(The mandatory argument for "long format" options are also 
mandatory for the correspondient sort option)
      
  -h, --help 
      show this help
  -n, nopasswd
      don't ask for the password when change to a "mode" if we are root.
  -t, test
      show the commands that will be executed, but don`t execute anything.
      This parameter is for testing or sintax checking.
  -f, --file = path 
      read and execute the commands in this file before enter 
      in interactive mode.
  -i, --init 
      this cli is the initial cli (login) so it must display 
      copyright, message of day, etc.
  -d, --directory = path 
      base path for extensions commands. Default is /etc/boscli/
  -r, --reference 
      generate the user manual as a html file


More info at: 
 * Bifer Operating System CLI developer Manual
 * Bifer Operating System CLI user Manual 
""" 
    print usage_msg


def initial_error(err_msg):
    print "Error."
    print err_msg
    print "Use: cli -h to see the how to use the command"
    sys.exit()


def handler(signum, frame):
    cli = get_cli()
    if cli != None:
        if cli.executing_command() == True:
            return
        try:
            bcli_exit([])
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
                                   "tnhf:id:ra", \
                                   ["test", "nopasswd", "help", "file=", \
                                    "init", "directory=", "reference"])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    command_file = None
    base_path = __default_base_path__
    initial_cli =  False
    generate_manual = False
    nopasswd_superuser = False
    test = False
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-t", "--test"):
            test = True
        elif opt in ("-n", "--nopasswd"):
            nopasswd_superuser = True
        elif opt in ("-f", "--file"):
            command_file = os.path.normpath(arg)
        elif opt in ("-d", "--directory"):
            base_path = os.path.abspath(os.path.normpath(arg))
        elif opt in ("-i", "--init"):
            initial_cli = True
        elif opt in ("-r", "--reference"):
            generate_manual = True
        else:
            initial_error ("%s, unhandled option" % opt)

    boscliutils.Log.init()
    boscliutils.Log.info("Starting boscli")

    # Open new CLI in normal mode
    cli = BiferShell(base_path, initial_cli, \
                     nopasswd_superuser, test)
    if command_file: cli.exec_cmds_file(command_file)
    
    
    
    
    if generate_manual:
        import manual
        manual.generate_html_user_doc()
        print "Manual generated"
    else:
        boscliutils.Log.info("Entering in interactive mode")
        cli.run()
    
    boscliutils.Log.info("End boscli")
