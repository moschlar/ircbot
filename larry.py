# -*- coding: iso-8859-1 -*-      
import MySQLdb                                                                                                                  
import sys                                                                                                                      
import socket                                                                                                                   
import string                                                                                                                   
import time                                                                                                                     
import commands                                                                                                                     
 
class Larry (object):
 
 #init
 def __init__(self):
  #IRC-Daten        
  self.HOST="134.93.63.201"
  self.PORT=6667           
  self.NICK="Larry"        
  self.IDENT="Larry"       
  self.REALNAME="Larry the Cow"
  self.CHANNEL="#public"       
 
  #Statusvariablen
  self.readbuffer=""
 
  #Initialisierung
  self.s=socket.socket( )
  self.s.connect((self.HOST, self.PORT))
  self.s.send("NICK %s\r\n" % self.NICK)
  self.s.send("USER %s %s bla :%s\r\n" % (self.IDENT, self.HOST, self.REALNAME))
  self.s.send("OPER Larry secretpasswd \r\n")                                 
  self.s.send("JOIN "+self.CHANNEL+'\r\n')                                      
 
 
 
  while 1:
    self.readbuffer=self.readbuffer+self.s.recv(128)
    temp=string.split(self.readbuffer, "\n")        
    self.readbuffer=temp.pop( )                     
 
    for line in temp:
        line=string.rstrip(line)
        line=string.split(line) 
        print line              
 
        #ping                   
        if(line[0]=="PING"):    
            #response to ping   
            self.s.send("PONG %s\r\n" % line[1])
            #force list channels                
            self.getChannels()                  
 
 
        #if channel listed
        if(line[1]=="322" and line[3][0]=="#"):
            #get channel and force list users  
            self.getUsers(line[3])             
 
        #if user listed
        if(line[1]=="352"):
            self.proceedUser(line[3],line[4],line[5],line[7])
 
        #if forced update
        if(line[1]=="PRIVMSG" and line[2]==self.NICK and line[3]==":update"):
            #force list channels                                             
            self.getChannels()                                               
 
        #if help                                                             
        if(line[1]=="PRIVMSG" and line[2]==self.NICK and line[3]==":help"):  
            #force list channels                                             
            self.printHelp(line[0])                                          
 
        #features
        if(line[1]=="PRIVMSG" and line[2]==self.NICK  and len(line)>4):
            if(line[3]==":house"):                                     
                self.dohouse(line[4],self.CHANNEL)                     
            if(line[3]==":say"):                                       
                cmd=""                                                 
                for i in line[4:]:                                     
                  cmd+=i+' '                                           
                self.s.send('PRIVMSG '+self.CHANNEL+' :'+cmd+' \r\n')  
 
 #force list channels
 def getChannels(self):
    self.s.send('LIST \r\n')
 
 #force list users
 def getUsers(self,channel):
    self.s.send('WHO '+channel+' \r\n')
 
 #op users or dont
 def proceedUser(self,channel,name,hostname,nick):
    print channel,name,hostname,nick              
    level=self.getLevel(channel,self.getIp(hostname))
    self.s.send( ' JOIN '+channel+' \r\n')           
    if level=="v" or level=="o":                     
      self.s.send( ' MODE '+channel+' +'+str(level)+' '+nick+' \r\n')
 
 #get users ip
 def getIp(self,hostname):
    if hostname == "www-v":
      return "134.93.63.201"
    s=commands.getstatusoutput('nslookup '+hostname)[1]
    ip=s.split('Address:')[-1].strip()                 
    if len(ip.split('.'))==4:                          
        return ip                                      
    else:                                              
        return "0.0.0.0"                               
 
 #get level by ip ord zdvname
 def getLevel(self,channel,ip):
    level="n"                  
 
    query="SELECT stat FROM irc WHERE user='"+ip+"' AND chan='"+channel[1:]+"'"
    res=self.getQuery(query)                                                   
    if len(res)>0:                                                             
      level=res[0][0]                                                          
 
    zdvname=self.getZdvName(ip)                                                
    print ip,zdvname                                                           
    if zdvname != None:                                                        
      query="SELECT stat FROM irc WHERE user='"+zdvname+"' AND chan='"+channel[1:]+"'"
      res=self.getQuery(query)                                                        
      if len(res)>0:                                                                  
        level=res[0][0]                                                               
 
    return level
 
 #get zdvname
 def getZdvName(self,ip):
    zdvname=None         
    query="SELECT zdvuser FROM host WHERE ipv4='"+ip+"'"
    res=self.getQuery(query)                            
    if len(res)>0:                                      
      zdvname=res[0][0]                                 
 
    return zdvname                                      
 
 #mysql query
 def getQuery(self,query):
    conn = MySQLdb.connect (host = "134.93.63.227", user = "irc", passwd = "secretpasswd", db = "userdbv3")        
    cursor = conn.cursor ()                                                                                          
    cursor.execute (query )                                                                                          
    answer = cursor.fetchall()                                                                                       
    cursor.close()                                                                                                   
    conn.close()                                                                                                     
 
    return answer                                                                                                    
 
 #dohouse feature                                                                                   
 def dohouse(self,nick,channel):                                                                    
    self.s.send(' NICK MCLarry \r\n ')                                                              
    self.NICK='MCLarry'                                                                             
    self.s.send(' PRIVMSG '+channel+' :and I say whose house? \r\n')                                
    time.sleep(2)                                                                                   
    self.s.send(' PRIVMSG '+channel+' :'+nick+'\'s house! \r\n')                                    
    time.sleep(2)                                                                                   
    self.s.send(' PRIVMSG '+channel+' :I say whose house? \r\n')                                    
    time.sleep(2)                                                                                   
    self.s.send(' PRIVMSG '+channel+' :'+nick+'\'s house! \r\n')                                    
    time.sleep(2)                                                                                   
    self.s.send(' PRIVMSG '+channel+' :I say whose house? \r\n')
    time.sleep(2)
    self.s.send(' PRIVMSG '+channel+' :say what? \r\n')
    time.sleep(2)
    self.s.send(' PRIVMSG '+channel+' :'+nick+'\'s house! \r\n')
    time.sleep(2)
    self.s.send(' KILL Larry :Klau nicht meinen Nick \r\n')
    self.NICK='Larry'
    self.s.send(' NICK Larry \r\n')
 
 
 
 #help
 def printHelp(self,nick):
 
 
    help0="/msg Larry update - erzwinge Operatorstatusupdate jetzt"
    help1="/msg Larry house  - highlighte in Housemodus "
    help2="/msg Larry say    - sprich durch Larry zur Welt"
 
    nick = nick.split("!")[0][1:]
    self.s.send(' PRIVMSG '+nick+' :'+help0+'\r\n')
    self.s.send(' PRIVMSG '+nick+' :'+help1+'\r\n')
    self.s.send(' PRIVMSG '+nick+' :'+help2+'\r\n')
 
 
 
L=Larry()