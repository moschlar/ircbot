import commands
import time

def startBot():
    s=commands.getstatusoutput("python /home/moschlar/ircbot/testbot.py")

def isBotAlive():
    s=commands.getstatusoutput("ps aux | grep testbot.py | grep -v grep | wc -l")
    return int(s[1]) > 0
 
if not isBotAlive():
    startBot()