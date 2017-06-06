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
    import gi
    gi.require_version('Notify', '0.7')
    from gi.repository import Gio, GLib, Notify
except ImportError:
    print('Package python3-gobject-base is missing.')
    print('Please install it using "dnf install python3-gobject-base".')
    sys.exit(1)
except ValueError:
    print('Please ensure that libnotify is version 0.7.')
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
        logger.error("Default gateway not found or " +
                     "system not connected to any network")
        return "NotSet"
    return str(gateway.group(1))


def notify(msg):
    Notify.init('proxyzap')
    notif = Notify.Notification.new(
      'proxyzap',  # titre
      msg,  # message
      'dialog-information'  # icon
    )
    notif.show()


class GnomeProxy(object):

    '''
    Manipulate Gnome proxy using gsettings

    Info from :
    https://wiki.archlinux.org/index.php/Proxy_settings#Proxy_settings_on_GNOME3
    https://marianochavero.wordpress.com/2012/04/03/short-example-of-gsettings-bindings-in-python/
    https://developer.gnome.org/gio/2.30/GSettings.html#g-settings-set-value
    '''

    def __init__(self, PROXY, PROXYPORT, PROXYIGNORE):
        ''' Initialize GnomeProxy
        Set proxy values

        :param PROXY: proxy hostname
        :type mode: str

        :param PROXYPORT: proxy port number
        :type mode: int

        :param PROXYIGNORE: hosts or subnets that do not require
        a proxy to connect to
        :type mode: list

        '''
        self.PROXY = PROXY
        self.PROXYPORT = PROXYPORT
        self.PROXYIGNORE = PROXYIGNORE
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
        ''' Retrieve proxy values '''
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
        '''
        Set proxy values

        :param mode: "manual" or "none"
        :type mode: str

        '''
        gsettings = Gio.Settings.new("org.gnome.system.proxy")
        gsettings.set_value(
                "mode",
                GLib.Variant('s', mode))
        msg = "Proxy has been set to %s" % mode
        notify(msg)
        logger.info(msg)

        if mode == 'manual':
            if self.proxy_ignore != self.PROXYIGNORE:
                # GLib.Variant('as', ['localhost', '127.0.0.0/8', '::1'])
                gsettings = Gio.Settings.new("org.gnome.system.proxy")
                gsettings.set_value(
                        "ignore-hosts",
                        GLib.Variant('as', self.PROXYIGNORE))

            if self.proxy_http_url != self.PROXY:
                gsettings = Gio.Settings.new("org.gnome.system.proxy.http")
                gsettings.set_value(
                        "host",
                        GLib.Variant('s', self.PROXY))
                gsettings.set_value(
                        "port",
                        GLib.Variant('i', self.PROXYPORT))
                gsettings = Gio.Settings.new("org.gnome.system.proxy.https")
                gsettings.set_value(
                        "host",
                        GLib.Variant('s', self.PROXY))
                gsettings.set_value(
                        "port",
                        GLib.Variant('i', self.PROXYPORT))
                gsettings = Gio.Settings.new("org.gnome.system.proxy.ftp")
                gsettings.set_value(
                        "host",
                        GLib.Variant('s', self.PROXY))
                gsettings.set_value(
                        "port",
                        GLib.Variant('i', self.PROXYPORT))
                logger.debug("Values : PROXY: %s, PORT: %s" % (
                        self.PROXY,
                        self.PROXYPORT))
                logger.debug("Ignoring proxy for : %s" % (str.join(
                    ',', self.PROXYIGNORE)))

        self.get_proxy_settings()

    def get_mode(self):
        return self.proxy_mode


class DnfProxy(object):

    '''
    Manipulate dnf proxy settings
    works only with http proxies
    '''

    def __init__(self):

        self.protocol = None
        self.host = None
        self.port = None
        self.dnf_config_path = "/etc/dnf/dnf.conf"
        self.get_proxy_settings()

    def get_proxy_settings(self):

        dnfconf = configparser.ConfigParser()
        try:
            with open(self.dnf_config_path, 'r') as f:
                dnfconf.read_file(f)
        except:
            msg = "DNF configuration file %s missing or invalid" \
                    % self.dnf_config_path
            logger.error(msg)
            sys.exit(1)

        if dnfconf.has_section('main'):
            if dnfconf.has_option('main', 'proxy'):
                protocol, host, port = dnfconf.get('main', 'proxy') \
                        .replace("//", "").split(":")
                self.protocol = protocol
                self.host = host
                self.port = port
        else:
            msg = "%s: missing section 'main'" % self.dnf_config_path
            logger.error(msg)

    def get_config(self):
        conf = {
                'protocol': self.protocol,
                'host': self.host,
                'port': self.port
                }
        return conf

    def set_proxy_settings(self, proxy, port):
        ''' Set proxy values inf dnf.conf file

        '''
        dnfconf = configparser.ConfigParser()
        try:
            dnfconf.read(self.dnf_config_path)

            if dnfconf.has_section('main'):
                url = 'http' + '://' + proxy + ':' + str(port)
                dnfconf.set('main', 'proxy', url)
                with open(self.dnf_config_path, 'w') as f:
                    dnfconf.write(f)
                self.get_proxy_settings()
                msg = "Dnf proxy has been configured"
                logger.info(msg)
            else:
                msg = "%s: missing section 'main'" % self.dnf_config_path
                logger.error(msg)

            self.get_proxy_settings()
        except:
            msg = "DNF configuration file %s missing or invalid" \
                % self.dnf_config_path
            logger.error(msg)
            sys.exit(1)

    def unset_proxy_settings(self):
        ''' Unset proxy settings in dnf.conf file

        '''
        dnfconf = configparser.ConfigParser()
        dnfconf.read(self.dnf_config_path)

        if dnfconf.has_section('main'):
            if dnfconf.has_option('main', 'proxy'):
                dnfconf.remove_option('main', 'proxy')
                with open(self.dnf_config_path, 'w') as f:
                    dnfconf.write(f)

        else:
            msg = "%s: missing section 'main'" % self.dnf_config_path
            logger.error(msg)

        self.get_proxy_settings()


############################################################
# MAIN
############################################################
if __name__ == "__main__":
    '''Main application proxyzap'''

    DNF_PROXY_CONTROL = False
    os.chdir(os.path.dirname(sys.argv[0]))

    config = configparser.ConfigParser()
    try:
        config.read_file(open('proxyzap.conf'))

        # Create logger
        if config['proxyzap']['DEBUG'] == 'True':
            logger = initialize_logger('proxyzap.log', 'nolog', logging.DEBUG)
        else:
            logger = initialize_logger('proxyzap.log', 'nolog', logging.INFO)

        # Do we control DNF config ?
        if config['proxyzap']['ENABLEPROXYDNF'] == 'True':
            DNF_PROXY_CONTROL = True

        # Get configuration values
        SUBGW, PROFILE = \
            config["proxyzap"]["SUBGW"].replace('"', '').split(':')

        PROXY = config[PROFILE]["PROXY"].replace('"', '')
        PROXYPORT = int(config[PROFILE]["PROXYPORT"].replace('"', ''))
        PROXYIGNORE = config[PROFILE]["PROXYIGNORE"].split(',')

    except (FileNotFoundError) as e:  # noqa
        print('Configuration file not found.')
        sys.exit(1)
    except (KeyError) as e:
        print('Configuration file invalid key ' +
              '{} is missing or not spelled correctly'.format(e))
        sys.exit(1)
    except (ValueError) as e:
        print('SUBGW profile is not defined. ex: SUBGW = 192.168.0.254:work')
        sys.exit(1)

    while 1:
        logger.debug("#### START LOOP ####")
        gateway = get_gw()
        logger.debug("Gateway is %s" % gateway)

        proxy_settings = GnomeProxy(PROXY, PROXYPORT, PROXYIGNORE)

        if DNF_PROXY_CONTROL:
            dnf_proxy = DnfProxy()

        logger.debug("Proxy mode is %s" % proxy_settings.get_mode())

        if SUBGW == gateway:
            logger.debug(
                    "Gateway (%s) is matching proxyzap SUBGW (%s) "
                    "configuration"
                    % (gateway, SUBGW))
            if proxy_settings.get_mode() != 'manual':
                proxy_settings.set_proxy_settings("manual")
            else:
                logger.debug("Proxy already set to manual")

            if DNF_PROXY_CONTROL:
                if (not dnf_proxy.get_config()['host'] == PROXY) or \
                   (not int(dnf_proxy.get_config['port']) == PROXYPORT):
                    dnf_proxy.set_proxy_settings(PROXY, PROXYPORT)
                else:
                    logger.debug("DNF Proxy already configured")

        else:
            if proxy_settings.get_mode() != 'none':
                proxy_settings.set_proxy_settings("none")
            else:
                logger.debug("Proxy already set to none")

            if DNF_PROXY_CONTROL:
                if not dnf_proxy.get_config()['host'] == None:
                    dnf_proxy.unset_proxy_settings()
                else:
                    logger.debug("DNF Proxy already unset")

        logger.debug("#### END LOOP ####")
        time.sleep(10)
