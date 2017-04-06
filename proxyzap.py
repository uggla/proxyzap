#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#
# Small script to update proxy settings on Gnome 3.
# The target system is Fedora 24/25.
# Goal is to update proxy settings as soon as connected on
# a specific subnet/gateway.

import subprocess
import re
import time
import configparser
import sys
import os
import logging
from logging.handlers import RotatingFileHandler
try:
    from gi.repository import Gio, GLib
except ImportError:
    print('Package python3-gobject-base is missing.')
    print('Please install it using "dnf install python3-gobject-base".')
    sys.exit(1)


def initialize_logger(LOGFILE,
                      CONSOLE_LOGGER_LEVEL,
                      FILE_LOGGER_LEVEL,
                      logger_name=None):
    '''Initialize a global logger to track application behaviour

    :param LOGFILE: Log filename
    :type LOGFILE: str
    :param CONSOLE_LOGGER_LEVEL: Console log level
                                (logging.DEBUG, logging.ERROR, ..) or nolog
    :type CONSOLE_LOGGER_LEVEL: logging constant or string
    :param FILE_LOGGER_LEVEL: File log level
    :type FILE_LOGGER_LEVEL: logging constant
    :returns:  logging object

    '''

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s :: %(levelname)s :: %(message)s')

    try:
        file_handler = RotatingFileHandler(
            os.path.expandvars(LOGFILE), 'a', 1000000, 1)
    except IOError:
        print('ERROR: {} does not exist or is not writeable.\n'.format(
            LOGFILE))
        print('       Try to create directory {}'.format(os.path.dirname(
            LOGFILE)))
        print('       using: mkdir -p {}'.format(os.path.dirname(
            LOGFILE)))
        sys.exit(1)

    # First logger to file
    file_handler.setLevel(FILE_LOGGER_LEVEL)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Second logger to console
    if CONSOLE_LOGGER_LEVEL != 'nolog':
        steam_handler = logging.StreamHandler()
        steam_handler.setLevel(CONSOLE_LOGGER_LEVEL)
        logger.addHandler(steam_handler)
    return logger


def get_gw():
    # Retrieve default route
    cmd = 'ip route show'
    route = subprocess.check_output(
            cmd.split()).decode('utf-8').split('\n')
    gateway = re.search(r'default via (\d+.\d+.\d+.\d+)', route[0])
    if not gateway:
        print("Default gateway not found")
        logger.critical("Default gateway not found")
        sys.exit(1)
    return gateway


class GnomeProxy(object):

    """Manipulate Gnome proxy using gsettings"""

    def __init__(self):
        self.proxy_mode = None
        self.proxy_ignore = None
        self.proxy_http_url = None
        self.proxy_http_port = None
        self.proxy_https_url = None
        self.proxy_https_port = None
        self.proxy_ftp_url = None
        self.proxy_ftp_port = None

        self.get_proxy_settings()

    def get_proxy_settings(self):
        """ Retrieve proxy values
        Info from :
        https://wiki.archlinux.org/index.php/Proxy_settings#Proxy_settings_on_GNOME3
        """
        gsettings = Gio.Settings.new("org.gnome.system.proxy")
        self.proxy_mode = str(
                gsettings.get_value("mode")).replace("'", "")
        self.proxy_ignore = str(
                gsettings.get_value("ignore-hosts")).replace("'", "")\
                                                    .replace('[', '')\
                                                    .replace(']', '')\
                                                    .split(',')

        gsettings = Gio.Settings.new("org.gnome.system.proxy.http")
        self.proxy_http_url = str(
                gsettings.get_value("host")).replace("'", "")
        self.proxy_http_port = str(
                gsettings.get_value("port")).replace("'", "")

        gsettings = Gio.Settings.new("org.gnome.system.proxy.https")
        self.proxy_https_url = str(
                gsettings.get_value("host")).replace("'", "")
        self.proxy_https_port = str(
                gsettings.get_value("port")).replace("'", "")

        gsettings = Gio.Settings.new("org.gnome.system.proxy.ftp")
        self.proxy_ftp_url = str(
                gsettings.get_value("host")).replace("'", "")
        self.proxy_ftp_port = str(
                gsettings.get_value("port")).replace("'", "")

    def set_proxy_settings(self, mode):
        ''' Initialize a global logger to track application behaviour

        :param mode: "manual" or "none"
        :type mode: str

        '''
        global PROXY, PROXYPORT, PROXYIGNORE

        gsettings = Gio.Settings.new("org.gnome.system.proxy")
        gsettings.set_value(
                "mode",
                GLib.Variant('s', mode))

        if mode == 'manual':
            if self.proxy_ignore != PROXYIGNORE:
                # GLib.Variant('as', ['localhost', '127.0.0.0/8', '::1'])
                gsettings = Gio.Settings.new("org.gnome.system.proxy")
                gsettings.set_value(
                        "ignore-hosts",
                        GLib.Variant('as', PROXYIGNORE))

            if self.proxy_http_url != PROXY:
                gsettings = Gio.Settings.new("org.gnome.system.proxy.http")
                gsettings.set_value(
                        "host",
                        GLib.Variant('s', PROXY))
                gsettings.set_value(
                        "port",
                        GLib.Variant('i', PROXYPORT))
                gsettings = Gio.Settings.new("org.gnome.system.proxy.https")
                gsettings.set_value(
                        "host",
                        GLib.Variant('s', PROXY))
                gsettings.set_value(
                        "port",
                        GLib.Variant('i', PROXYPORT))
                gsettings = Gio.Settings.new("org.gnome.system.proxy.ftp")
                gsettings.set_value(
                        "host",
                        GLib.Variant('s', PROXY))
                gsettings.set_value(
                        "port",
                        GLib.Variant('i', PROXYPORT))
        self.get_proxy_settings()

    def get_mode(self):
        return self.proxy_mode


############################################################
# MAIN
############################################################
if __name__ == "__main__":
    '''Main application proxyzap'''

    config = configparser.ConfigParser()
    try:
        config.read('proxyzap.conf')
    except:
        print('Configuration file not found or invalid')
        sys.exit(1)

    # Create logger
    if config['proxyzap']['DEBUG'] == 'True':
        logger = initialize_logger('proxyzap.log', 'nolog', logging.DEBUG)
    else:
        logger = initialize_logger('proxyzap.log', 'nolog', logging.INFO)

    # Get configuration values
    SUBGW = config["proxyzap"]["SUBGW"].replace('"', '')
    PROXY = config["proxyzap"]["PROXY"].replace('"', '')
    PROXYPORT = int(config["proxyzap"]["PROXYPORT"].replace('"', ''))
    PROXYIGNORE = config["proxyzap"]["PROXYIGNORE"].split(',')

    while 1:
        gateway = get_gw()
        logger.debug("#### START LOOP ####")
        logger.debug("Gateway is %s" % gateway.group(1))

        proxy_settings = GnomeProxy()
        logger.debug("Proxy mode is %s" % proxy_settings.get_mode())

        if SUBGW == gateway.group(1):
            logger.debug(
                    "Gateway (%s) is matching proxyzap SUBGW (%s) "
                    "configuration"
                    % (gateway.group(1), SUBGW))
            if proxy_settings.get_mode() != 'manual':
                proxy_settings.set_proxy_settings("manual")
                logger.info("Proxy has been set to manual")
                logger.debug(
                        "Values : PROXY: %s, PORT: %s" % (PROXY, PROXYPORT))
                logger.debug(
                        "Ignoring proxy for : %s" % (
                            str.join(',', PROXYIGNORE)))
            else:
                logger.debug("Proxy already set to manual")
        else:
            if proxy_settings.get_mode() != 'none':
                proxy_settings.set_proxy_settings("none")
                logger.info("Proxy has been set to none")
            else:
                logger.debug("Proxy already set to none")

        logger.debug("#### END LOOP ####")
        time.sleep(10)
