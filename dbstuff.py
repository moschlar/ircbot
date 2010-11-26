#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""Database connection for getting IRC user levels in IRC channels.

Uses sqlalchemy as database abstraction layer and the defined model here

@version: 0.2
@author: moschlar
"""

DEBUG = 0
VERSION = "0.2"


import sys
from os.path import exists, splitext
from ConfigParser import SafeConfigParser

#-----------------------------------------------------------------------------------
# Parsing Database Configuration
#-----------------------------------------------------------------------------------


config_file = "testbot.cfg"

config = SafeConfigParser()
config.read(config_file)

# Getting database information from config_file
try:
    db_engine = config.get("database","engine")
    db_server = config.get("database", "server")
    user = config.get("database", "user")
    passwd = config.get("database", "password")
    db = config.get("database", "database")
except:
    raise Exception("Could not read database path from %s" % config_file)

# Parsing database information to path-string
try:
    path_to_db = db_engine + "://"
    if user:
        path_to_db += user
        if passwd:
            path_to_db += ":" + passwd
        path_to_db += "@"
    path_to_db += db_server + "/"
    path_to_db += db
except:
    raise Exception("Could not parse path to database!")

if DEBUG: print path_to_db

#-----------------------------------------------------------------------------------

import socket

from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sqlalchemy.ext.declarative import declarative_base

#-----------------------------------------------------------------------------------
# Declaring the database model
#-----------------------------------------------------------------------------------

Base = declarative_base()
class irc(Base):
    __tablename__ = 'irc'
    
    id = Column(Integer, primary_key=True)
    chan = Column(String)
    user = Column(String)
    stat = Column(String)
    
class host(Base):
    __tablename__ = "host"
    
    id = Column(Integer, primary_key=True)
    zdvuser = Column(String)
    wohnheim = Column(Integer)
    hostname = Column(String)
    mac = Column(String)
    ipv4 = Column(String)
    ipv6 = Column(String)
    lastmod = Column(Integer)
    modby = Column(String)

#-----------------------------------------------------------------------------------

engine = create_engine(path_to_db, echo=False)
Session = sessionmaker(bind=engine)
session = Session()

#-----------------------------------------------------------------------------------
# The only function that makes this class useful
#-----------------------------------------------------------------------------------

def getLevel(channel,hostname):
    """Returns IRC user level from database.
    
    The database model is used through sqlalchemy as defined above.
    The first query tries to get an entry just by submitting the ip address,
    the second query joins the host.zdvuser which has the given ip address with 
    irc.user.
    """
    level = "n"
    
    if DEBUG: print channel
    if channel.startswith("#"):
        channel = channel[1:]
    if DEBUG: print hostname
    
    try:
        ip = socket.gethostbyname(hostname)
        if DEBUG: print ip
    except:
        return level
    
    q = session.query(irc.stat).filter(irc.user == ip).filter(irc.chan == channel).first()
    if q:
        if DEBUG: print "User level by ip address: %s" % q
        level = q[0]
    
#    This SQL query shall be performed:
#    
#    SELECT irc.`stat` FROM `irc`
#    LEFT JOIN `host` ON irc.`user` = host.`zdvuser`
#    WHERE host.`ipv4` = 'ip' AND irc.`chan` = 'channel'
    
    p = session.query(irc.stat).join((host, irc.user == host.zdvuser)).filter(host.ipv4 == ip).filter(irc.chan == channel).first()
    if p:
        if DEBUG: print "User level by ZDV-Username: %s" % p
        level = p[0]
    
    return level

#-----------------------------------------------------------------------------------
# And finally some test cases
#-----------------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print ("Usage: dbstuff.py #channel hostname")
    else:
        hostname = sys.argv[2]
        channel = sys.argv[1]
        level = getLevel(channel,hostname)
        print ("%s has mode +%c in %s" % (hostname,level,channel))
    
