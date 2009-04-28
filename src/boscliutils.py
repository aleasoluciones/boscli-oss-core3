#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Alea-Soluciones (Bifer) 2007, 2008, 2009
# Licensed under GPL v3 or later, see COPYING for the whole text

'''
  $Id:$
  $URL:$
  Alea-Soluciones (Bifer) (c) 2007
  Created: eferro - 11/11/2007

'''

import os, signal, sys
import logging
import logging.handlers
import subprocess
import boscli
import tempfile
import tailer
import threading,time


# Workaround to create static methods
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52304
class Callable:
    def __init__(self, anycallable):
        self.__call__ = anycallable


class Log:
    log_file = 'boscli.log'
    
    def init():
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)-15s boscli %(levelname)s %(message)s',
                            filename= Log.log_file,
                            filemode='a')
        
    def debug(msg):
        logging.debug(msg)

    def info(msg):
        logging.info(msg)
        
    def warning(msg):
        logging.warning(msg)

    def error(msg, exception):
        import traceback
        logging.error(msg)
        logging.error(''.join(traceback.format_list(traceback.extract_stack())))



    init = Callable(init)
    debug = Callable(debug)
    info = Callable(info)
    warning = Callable(warning)
    error = Callable(error)


class SOCommand:
    def __init__(self, cmd):
        self.__cmd = cmd
        self.__result = None
        self.__out = []
        self.__err = []
        self.run()

    def get_cmd(self):
        return self.__cmd
    
    def run(self):
        self.log_start()
        self.__result = self.execute()
        self.log_end()
    
    def result(self):
        return self.__result
    
    def execute(self):
        raise "Should be reimplemented by the descendants"
        
    def log_start(self):
        Log.debug("Executing: '%s'" % self.__cmd)
    def log_end(self):
        Log.debug("Executing end: '%s'" % self.__cmd)

class InteractiveCommand(SOCommand):
    def __init__(self, cmd):
        SOCommand.__init__(self, cmd)
        
    def execute(self):        
        # FIXME: cambiar a subprocess.call o similar teniendo en
        # cuenta el problema de los metacaracteres (> < |)
        return os.system(self.get_cmd())
    


def validate_filter(filter_str):
    filter = None
    if filter_str != None:
        filter = filter_str.strip().split()
    if filter != None:
        if len(filter) != 2 or not filter[0] in ['include', 'begin', 'exclude']:
            print "Error in filter expresion '%s'." % filter_str
            print "Use '(include | begin | exclude) regexp'"
            return False
    return True
    

class CmdInterrupted(Exception): pass

def cmd_signalhandler(signum, frame):
    raise CmdInterrupted


class BatchCommand(SOCommand):
    def __init__(self, cmd):
	SOCommand.__init__(self, cmd)
        self.w = None
        self.cmd_alive = False

    def __real_execute(self):        
        tmp_fd, tmp_name = tempfile.mkstemp('.tmp', 'cli-', '/tmp/')
        num_lines = 0
        
	try:
	    cmd_process = subprocess.Popen(self.get_cmd(),
                                           shell = True, 
                                           stdout = open(tmp_name, "w"), 
                                           close_fds = True)
            self.cmd_alive = True
            
            # While the process is alive, read its output and
            # write to the stdout
            f = open(tmp_name)
            line = ''
            while cmd_process.poll() == None:
                b = f.read(1)
                if b == '':
                    time.sleep(0.001)
                    continue
                if b == '\n':
                    print line
                    line = ''
                else:
                    line = line + b

            if len(line) != 0:
                # Write all pending bytes (allready readed)
                print line,

            # The process finish so we can read all the output
            # and wrote the rest of ouput to the stdout
            b = f.read()
            print b,

        except IOError, (errno, strerror):
            pass
        except CmdInterrupted:
            pass
        finally:

            while cmd_process.poll() == None:
                time.sleep(0.001)
            try:
                os.unlink(tmp_name)
            except:
                pass

        
    def execute(self):
        handler_sigterm = signal.getsignal(signal.SIGTERM)
        handler_sigint = signal.getsignal(signal.SIGINT)
        handler_sigtstp = signal.getsignal(signal.SIGTSTP)
        try:
            signal.signal(signal.SIGTERM, cmd_signalhandler)
            signal.signal(signal.SIGINT, cmd_signalhandler)
            signal.signal(signal.SIGTSTP, cmd_signalhandler)

            self.__real_execute()
            
        except IOError, (errno, strerror):
            pass
        except CmdInterrupted:
            pass
        finally:
            signal.signal(signal.SIGTERM, handler_sigterm)
            signal.signal(signal.SIGINT, handler_sigint)
            signal.signal(signal.SIGTSTP, handler_sigtstp)


def get_ch():
    import sys, tty, termios
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


class FilterOut:
    def __init__(self, out, regex, command, pager):
        """Filter|Pager class.
        command: 'include'|'exclude'|'begin'|None
        pager: True | False 
        """
        # The filter must be already validated
        self.__out = out
        self.__regex = regex
        self.__command = command
        self.__pager = pager
	self.__line = 1
        self.__text = ''

        try:
            import curses
            curses.setupterm()
            self.__num_lines = curses.tigetnum('lines')
	except KeyError:
            self.__num_lines = 24
        except:
            # If we have a problem to init the terminal
            # it is not an interactive session so we don't
            # use pager
            self.__pager = False

    def num_term_lines(self):
	return self.__num_lines


    def wait_term_character(self):
	# From http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/134892
	import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
            if ord(ch) == 3 or ord(ch) == 26:
                # The user press CTRL-C (ETX (end of text))/CTR-Z (ETB (end of trans. blk))
                # so we interrupt the command. This values are depending the raw protocol
                # of the terminal but this values are the more commons
                os.kill(os.getpid(), signal.SIGINT)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def flush():
        self.__out.write("FLUSH")
        self.__out.flush()
        if self.__textline != '':
            self.__out.write(self.__textline)
            self.__out.flush()
            self.__text = ''

    def output_line(self, line):
        if (self.__pager == True) and (self.__line == self.num_term_lines() - 1):
            # If we have pager and we allready show the max number of line
            # we show a prompt and wait for a key press
            self.__out.write("--MORE--\n")
            self.__out.flush()
            self.wait_term_character()
            self.__line = 1
    
        # Write the real line
        self.__out.write(line)
        self.__out.flush()
        self.__line = self.__line + 1

    def validate_line(self, line):
        text_ok = False
        if self.__command == 'include' and self.__regex in line: text_ok = True
        elif self.__command == 'exclude' and not self.__regex in line: text_ok = True
        elif self.__command == 'begin' and line.startswith(self.__regex): text_ok = True
        elif self.__command == None: text_ok = True
        return text_ok
    
    def write(self, text):
        self.__text = self.__text + text
        if self.__text[-1:] != '\n':
            return
        lines = self.__text.split('\n')
        for l in lines:
            if l == '':
                continue
            if self.validate_line(l):
                self.output_line(l + '\n')
        self.__text = ''



def follow_file(file_name, num_lines = 20):
    handler_sigterm = signal.getsignal(signal.SIGTERM)
    handler_sigint = signal.getsignal(signal.SIGINT)
    handler_sigtstp = signal.getsignal(signal.SIGTSTP)
    try:
        signal.signal(signal.SIGTERM, cmd_signalhandler)
        signal.signal(signal.SIGINT, cmd_signalhandler)
        signal.signal(signal.SIGTSTP, cmd_signalhandler)

        for line in tailer.tail(open(file_name), num_lines):
            print line
        for line in tailer.follow(open(file_name), delay=0.01):
            print line

    except IOError, (errno, strerror):
        pass
    except CmdInterrupted:
        pass
    finally:
        signal.signal(signal.SIGTERM, handler_sigterm)
        signal.signal(signal.SIGINT, handler_sigint)
        signal.signal(signal.SIGTSTP, handler_sigtstp)

# FIXME bifer system dep
def distrib_version():
    # Example:
    # /etc/lsb-release (content)
    # DISTRIB_ID=UbuntuBos
    # DISTRIB_RELEASE=7.04-0.2
    # DISTRIB_CODENAME=loe (living on the edge)
    # DISTRIB_DESCRIPTION="UbuntuBos 7.04-0.2"
    
    version = None
    for l in open('/etc/lsb-release', 'r'):
        if l.startswith('DISTRIB_RELEASE'):
            version = l.split('=')[1][:-1]
    return version

def distrib_majorversion():
    return distrib_version().split('-')[0]

def distrib_minorversion():
    try:
        minorversion = distrib_version().split('-')[1]
        return minorversion        
    except IndexError:
        return ''


def apache_enable_site(site):
    os.popen("ln -s /etc/apache2/sites-available/%s /etc/apache2/sites-enabled/%s" % (site, site)).readlines()
    os.popen("/etc/init.d/apache2 reload").readlines()

def apache_disable_site(site):
    os.popen("rm /etc/apache2/sites-enabled/%s" % site).readlines()    
    os.popen("/etc/init.d/apache2 reload").readlines()




def ngrep(eth, port, mta):
    BatchCommand("ngrep -d %s  -l port %d and host %s" % (eth, port, mta))
def ngrep_byline(eth, port, mta):
    BatchCommand("ngrep -d %s  -W byline -l port %d and host %s" % (eth, port, mta))

    
def main():
    pass

    
if __name__ == '__main__':
    main()
