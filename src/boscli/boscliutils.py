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
import syslog
import subprocess
import boscli
import tempfile
import threading,time


class Log:
    Name = ''
    Verbose = False
    Debug = False

    def init(name, verbose, debug):
        Log.Name = name
        Log.Verbose = verbose
        Log.Debug = debug
        syslog.openlog(name)

    @staticmethod
    def debug(msg):
        if Log.Debug:
            syslog.syslog(syslog.LOG_DEBUG, msg)

    @staticmethod
    def log(msg):
        syslog.syslog(syslog.LOG_INFO, msg)

    @staticmethod
    def info(msg):
        if Log.Verbose or Log.Debug:
            syslog.syslog(syslog.LOG_INFO, msg)

    @staticmethod
    def warning(msg):
        print(msg)
        syslog.syslog(syslog.LOG_WARNING, msg)

    @staticmethod
    def error(msg, exception):
        import traceback
        syslog.syslog(syslog.LOG_ERR, msg)
        syslog.syslog(syslog.LOG_ERR, ''.join(traceback.format_list(traceback.extract_stack())))
        traceback.print_exc()


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
        # FIXME: change to subprocess.call or similar.
        return os.system(self.get_cmd())



def validate_filter(filter_str):
    filter = None
    if filter_str != None:
        filter = filter_str.strip().split()
    if filter != None:
        if len(filter) != 2 or not filter[0] in ['include', 'begin', 'exclude']:
            print("Error in filter expresion '%s'." % filter_str)
            print("Use '(include | begin | exclude) regexp'")
            return False
    return True


class CmdInterrupted(Exception): pass

def cmd_signalhandler(signum, frame):
    raise CmdInterrupted


class BatchCommand(SOCommand):
    def __init__(self, cmd):
        SOCommand.__init__(self, cmd)

    def __real_execute(self):
        try:
            cmd_process = subprocess.Popen(self.get_cmd(),
                                           shell = True,
                                           stdout = subprocess.PIPE,
                                           stderr = subprocess.STDOUT,
                                           close_fds = True)
            while True:
                line = cmd_process.stdout.readline()
                if not line:
                    break
                print(line)

        except (IOError, (errno, strerror)):
            pass
        except CmdInterrupted:
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

        except (IOError, (errno, strerror)):
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

    def flush(self):
        if self.__text != '':
            self.__out.write(self.__text)
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
        self.__out.write(line + '\n')
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
        lines = self.__text.splitlines()
        for l in lines:
            if self.validate_line(l):
                self.output_line(l)
        self.__text = ''


def main():
    pass


if __name__ == '__main__':
    main()
