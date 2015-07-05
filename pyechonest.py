#!/usr/bin/env python
# coding=utf-8
#
# Copyright 2015 Arn-O. See the LICENSE file at the top-level directory of this
# distribution and at
# https://github.com/Arn-O/py-kodi-remote-controller/blob/master/LICENSE.

'''
Kodi remote controller in command lines based on (cmd). Integrated with
the echonest API for smart playlists generation.
More info on the echonest API: http://developer.echonest.com/docs/v4
'''

import cmd
import logging
import argparse
import pickle

logger = logging.getLogger(__name__)

# utility functions

def get_params():
    '''Get the run parameters'''
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbosity",
            action="count",
            help='Increase output verbosity')
    args = parser.parse_args()
    if args.verbosity == 2:
        logging.basicConfig(level=logging.DEBUG)
    else:
        if args.verbosity == 1:
            logging.basicConfig(level=logging.INFO)
            logger.info('Kodi controller started in verbosity mode ...')
            logger.debug('... and even in high verbosity mode!')
    return 

def is_file(fname):
    '''Return true if the file does exist'''
    logger.debug('call function is_file')
    try:
        open(fname)
    except IOError:
        return False
    return True

def input_params():
    '''Request the user for params input'''
    logger.debug('call function input_params')
    params = {}
    params['ip'] = raw_input("Kodi server IP: ")
    params['port'] = raw_input("Kodi server port: ")
    params['user'] = raw_input("Kodi server user: ")
    params['password'] = raw_input("Kodi server password: ")
    params['echonest_key'] = raw_input("Echonest developer key: ")
    return params

def save_params(params):
    '''Save the Kodi parameters to a local file'''
    logger.debug('call function save_params')
    f = open('params.pickle', 'wb')
    pickle.dump(params, f)
    f.close()

def read_params():
    '''Read the Kodi params from the local file'''
    logger.debug('call function read_params')
    f = open('params.pickle', 'rb')
    params = pickle.load(f)
    f.close()
    return params

def display_banner():
    '''Display initial banner'''
    logger.debug('call function display_banner')
    print "No Kodi params file found, this is probably the first launch. Check"
    print "your Kodi parameters (IP, port, user and password) and create an"
    print "Echonest account: https://developer.echonest.com/account/register"
    print
    print "Read the API key on the Echonest account, it will be requested"
    print "later on. When you are ready, try params_create."

class KodiRemote(cmd.Cmd):
    
    def preloop(self):
        get_params()
        if is_file('params.pickle'):
            logger.debug('kodi params file found')
            self.params = read_params()
        else:
            logger.info('no kodi params file')
            print
            display_banner()
            print

    # Kodi params file

    def do_params_create(self, line):
        '''
        Create the Kodi params file.
        Usage: params_create
        '''
        logger.debug('call function do_params_create')
        print
        self.params = input_params()
        print
        save_params(self.params)

    def do_params_display(self, line):
        '''
        Display the Kodi params file.
        Usage: params_display
        '''
        logger.debug('call function do_params_display')
        print
        print "Kodi parameters:"
        print "   Network:    %s/%s" % (
                self.params['ip'], 
                self.params['port'])
        print "   Credential: %s (%s)" % (
                self.params['user'], 
                self.params['password'])
        print
        print "Echonest API key: %s" % self.params['echonest_key']
        print

    def do_EOF(self, line):
        '''Override end of file'''
        logger.info('Bye!')
        print 'Bye!'
        return True

def main():
    '''Where everything starts'''

    remote_controller = KodiRemote()
    remote_controller.cmdloop()

if __name__ == '__main__':
    main()
