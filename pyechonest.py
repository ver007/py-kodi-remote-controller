#!/usr/bin/env python
# coding=utf-8
#
# Copyright 2015 Arn-O. See the LICENSE file at the top-level directory of this
# distribution and at
# https://github.com/Arn-O/py-kodi-remote-controller/blob/master/LICENSE.

import cmd
import logging
import argparse

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

class KodiRemote(cmd.Cmd):
    
    def preloop(self):
        get_params()

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
