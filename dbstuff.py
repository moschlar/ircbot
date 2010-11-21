'''
Created on 20.11.2010

@author: moschlar
'''

CONFIG_FILE = "testbot.cfg"
path_to_db = "sqlite:///:memory:"

from ConfigParser import SafeConfigParser
config = SafeConfigParser()
config.read(CONFIG_FILE)

db_engine = config.get("database","engine")
db_server = config.get("database", "server")
user = config.get("database", "user")
passwd = config.get("database", "passwd")
db = config.get("database", "database")

if db_engine == "mysql":
    path_to_db = "mysql://"
    if user:
        path_to_db += user
        if passwd:
            path_to_db += ":" + passwd
        path_to_db += "@"
    path_to_db += db_server + "/"
    path_to_db += db

import socket

from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sqlalchemy.ext.declarative import declarative_base

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

engine = create_engine(path_to_db, echo=False)
Session = sessionmaker(bind=engine)
session = Session()

def getLevel(channel,hostname):
    level = "n"
    #print channel
    if channel.startswith("#"):
        channel = channel[1:]
    #print hostname
    ip = socket.gethostbyname(hostname)
    #print ip
    q = session.query(irc.stat).filter(irc.user == ip).filter(irc.chan == channel).first()
    #print "q: %s"%q
    
    if q:
        level = q[0]
    
    p = session.query(host.zdvuser).filter(host.ipv4 == ip).first()
    #print "p: %s"%p
    
    if p:
        p = p[0]
        r = session.query(irc.stat).filter(irc.user == p).filter(irc.chan == channel).first()
        #print "r: %s"%r
        if r:
            level = r[0]
    
    return level

def getChannelLevels(channel):
    
    levels = {}
    
    #print channel
    if channel.startswith("#"):
        channel = channel[1:]
        
    q = session.query(irc.user,irc.stat).filter(irc.chan == channel).all()
    #print q
    
    # Lets make a nice dictionary out of the tuples
    for (user,mode) in q:
        levels[user] = mode
    
    return levels

if __name__ == "__main__":
    #print getLevel("#public","stewie.k3.wohnheim.uni-mainz.de")
    #print getLevel("#public","134.93.136.6")
    #print getLevel("#k3","134.93.136.6")
    print getChannelLevels("#public")