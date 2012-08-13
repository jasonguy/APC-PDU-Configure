"""
This module is used to mass configure APC Power Distribution Units (PDU).

The config file is downloaded (via ftp) and stored in 'configs/<ip>.ini' file. The 
config can then be parsed, modified, stored and sent back to the respective PDU.

Take care that after the config file is written, it should not be updated on the remote 
PDU system for a few minutes, as the PDU seems to randomly scan for changed configs 
and apply them at varying rates. There is not much information available on how this 
works from APC.

Usage examples are included in example.py.  

This is the python port (with a few changes) of the orignial php code written by 
Kevin O'Connor <kjoconnor@gmail.com>

For further documentation and updated code : https://github.com/raags/APC-PDU-Configure
"""

import os
import re
import sys
from datetime import datetime
from ftplib import FTP

VERSION = '1.0'

class ApcPdu(object):
    """
    Main class to be used to retreive, modify and push 
    configuration for APC Power Distribution Units (PDU)
    
    Configuration file 'config.ini' is downloaded via ftp
    
    Example::
    >>> from apc import ApcPdu
    >>> pdu = ApcPdu('192.168.1.1', 'apc', 'apc')
    >>> pdu.connect()
    >>> pdu.getConfig()
    >>> pduConfig = pdu.parseConfig()
    >>> pduConfig['SystemID']['Contact'] = 'Testing'
    >>> pdu.writeConfig(pduConfig)
    >>> pdu.close()
    """
    
    def __init__(self, ipaddress, username, password):
        self._connected = False
        self.ip = ipaddress
        self.username = username
        self.password = password
    
    def get_ip(self):
        return self._ip
    
    def set_ip(self, ipaddress):
        ipreg = re.compile('^(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]\d|\d)(?:[.](?:25[0-5]|2[0-4]\d|1\d\d|[1-9]\d|\d)){3}')

        if not ipreg.match(ipaddress):
            raise ValueError(ipaddress + " is not a valid address")
            
        self._ip = ipaddress
        
    ip = property(get_ip, set_ip)

    def exit(self):
        if (self.connected):
            self.close()

    def connect(self):
        """Opens a ftp connection to the PDU FTP server."""

        self._ftpConnection = FTP(self.ip)
        self._ftpConnection.login(self.username, self.password)
        self._connected = True

    def getConfig(self):
        """Downloads config from PDU and stores in 'configs/<ip>.ini'."""
        
        if(not self._connected):
            raise Exception("Can't get config without being connected first")
        
        if not os.path.exists('configs'):
                os.mkdir('configs')
                
        configFile = open('configs/' + self.ip + '.ini', 'w')
        
        self._ftpConnection.retrlines('RETR config.ini', lambda line: configFile.write('%s\n' % line))

        #if(file_exists('configs/' + self._ip + '.ini')):
        #   return True

        #sys.stderr.write("Transfer appeared successful but config does not exist.")
        #return False

    def close(self):
        """Closes the open connection"""
        
        if(self._connected):
            self._ftpConnection.quit()
            self._ftpConnection = False
            self._connected = False    
        else:
            raise Exception("Tried to close non-existent connection")

    def parseConfig(self):
        """Parses 'configs/<ip>.ini' into an array of config directives and values.
        
        The syntax is config[directive][item] = value, where:
        directive - is something like [NetworkTCP/IP] that's in a regular config.ini 
        item - is what goes on the left side of the config line 
        value - is the right side
        """
        
        configFile = open('configs/' + self.ip + '.ini', 'r')

        if os.stat('configs/' + self.ip + '.ini')[6]==0:
            raise Exception("Config file is empty")

        config = {}
        configDirective = ''

        for line in configFile:
            line = line.strip()

            # Filter out comments
            if line.startswith(';'):
                continue

            # Filter out blank lines
            if(line == ''):
                continue

            # Config directive
            if line.startswith('['):
                configDirective = line.split('[')[1].split(']')[0]   # Gets text between [], TODO : make this better
                config[configDirective] = {}
                continue

            # Looks to be a regular config directive
            # Split on = and place into config array

            lineSplit = line.split("=")

            config[configDirective][lineSplit[0]] = lineSplit[1]

            lineSplit=""

        configFile.close()
        return config


    def writeConfig(self, config):
        """Writes the passed config dictionary to 'configs/<ip>.ini' file, 
        and uploads it to the remote pud via ftp.
        """
        
        if not self._connected:
            raise Exception("Can't write config when not connected")

        toWrite  = "; Config written at " + str(datetime.now()) + "\n"
        toWrite += "; PDU writer version " + VERSION + "\n"
        toWrite += "; Original Author : 2011 Kevin O'Connor - kjoconnor@gmail.com\n"
        toWrite += "; Python Conversion : 2012 Raghu Udiyar - raghusiddarth@gmail.com\n"

        for configDirective in config:
            toWrite += '[' + configDirective + "]\n"

            configLine = config[configDirective]

            for line in configLine:
                toWrite += line + "=" + configLine[line] + "\n"
            
        with open('configs/' + self.ip + '.ini_updated', 'w') as configFile:
            configFile.write(toWrite)
        
        with open('configs/' + self.ip + '.ini_updated') as configFile:
            self._ftpConnection.storlines('STOR config.ini', configFile)
