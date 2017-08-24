#!/usr/bin/env python
#coding=utf-8
import os
import subprocess
import string
import time
import datetime
import sys
import math
import re
import linecache
import multiprocessing
import threading
import Queue
import logging
import paramiko
import  shelve

from multiprocessing import Process
from optparse import OptionParser

reload(sys) 
sys.setdefaultencoding('utf-8')

LGWMODELIST = {
    "NAT": "0",
    "ROUTER": "1",
    "BRIDGE": "2"}

# set cell cmds
SETLGWCMD = "cli -c 'oam.set LTE_LGW_TRANSFER_MODE %s'"
SETSACMD = "cli -c 'oam.set LTE_TDD_SUBFRAME_ASSIGNMENT %s'"
SETSPCMD = "cli -c 'oam.set LTE_TDD_SPECIAL_SUB_FRAME_PATTERNS %s'"
GETLGWCMD = "cli -c 'oam.getwild LTE_LGW_TRANSFER_MODE' | awk -F ' ' '{print $2}'  | tr -d '\n'"
GETSACMD = "cli -c 'oam.getwild LTE_TDD_SUBFRAME_ASSIGNMENT' | awk -F' ' '{print $2}' | tr -d '\n'"
GETSPCMD = "cli -c 'oam.getwild LTE_TDD_SPECIAL_SUB_FRAME_PATTERNS' | awk -F' ' '{print $2}' | tr -d '\n'"

# common
ISOTIMEFORMAT='%Y-%m-%d-%X'
MAILIST = ["lipeng-T@baicells.com"]
HOMEDIR = sys.path[0]

# cell route
CELLROTE= ["if route -n | grep -q 10.0.10.0;then :;else route add -net 10.0.10.0/24 gw 192.168.9.46;fi",
           "if route -n | grep -q 100.0.100.0;then : ;else route add -net 100.0.100.0/24 gw 192.168.9.56;fi",
           "if route -n | grep -q 123.1.1.0 ;then :;else route add -net 123.1.1.0/24 gw 192.168.9.57;fi"]

# FTP route
FTPROUTE1 = "route add -net 10.10.10.0/24 gw 192.168.9.42"
FTPROUTE2 = "ifconfig em1:ftp%s inet 123.1.1.%s netmask 255.255.255.255 up"
    

def do_clicmd(hostname, command, username="root", password="root123",
              port="27149"):
    '''
    Set the basic configuration in cli.txt.	
    hostname: the conneced host IP address		
    username: login host name		
    password: login host password	
    path: storage path of the configuration script and log
    '''
    try:
        port = int(port)	
        client=paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, port, username, password)	
        stdin,stdout,stderr=client.exec_command("%s" % command)
        returncode=stdout.read()
        client.close()
        return returncode
    except:
        return "ERROR"

def cellsetting(inputargs, ftpargs):
    # lgw seting
    lgwnow = do_clicmd(str(ftpargs["chost"]),"root",str(ftpargs["csshpw"]),
                       ftpargs["cport"],GETLGWCMD)
    if lgwnow is LGWMODELIST[inputargs["lgwmode"]] :
        logger.info("Lgw mode is %s already" % inputargs["lgwmode"])
    else:
        lgwcmd = SETLGWCMD % LGWMODELIST[inputargs["lgwmode"]]
        returncode = do_clicmd(str(ftpargs["chost"]),"root",str(ftpargs["csshpw"]),
                               ftpargs["cport"],lgwcmd)
        print returncode
        if returncode is "":
            logger.info("Lgw mode is setting %s now" % inputargs["lgwmode"]) 
        else:
            logger.error("Lgw mode is setting fail")
            exit(1)
    # sa setting
    sanow = do_clicmd(str(ftpargs["chost"]),"root",str(ftpargs["csshpw"]),
                       ftpargs["cport"],GETSACMD)
    if sanow is inputargs["subframe"]:
        logger.info("SA is %s already" % inputargs["subframe"])
    else:
        sacmd = SETSACMD % inputargs["subframe"]
        returncode = do_clicmd(str(ftpargs["chost"]),"root",str(ftpargs["csshpw"]),
                               ftpargs["cport"],sacmd)
        if returncode is "":
            logger.info("SA is setting %s now" % inputargs["subframe"])
        else:
            logger.error("SA is setting fail")
            exit(1)
    # sp setting
    spnow = do_clicmd(str(ftpargs["chost"]),"root",str(ftpargs["csshpw"]),
                       ftpargs["cport"],GETSPCMD)
    if spnow is inputargs["sspframe"]:
        logger.info("SP is %s already" % inputargs["sspframe"])
    else:
        spcmd = SETSPCMD % inputargs["sspframe"]
        returncode = do_clicmd(str(ftpargs["chost"]),"root",str(ftpargs["csshpw"]),
                               ftpargs["cport"],spcmd)
        if returncode is "":
            logger.info("SP is setting %s now" % inputargs["sspframe"])
        else:
            logger.error("SP is setting fail")
            exit(1)
    return

def setcellroute(host="192.168.9.149",user="root",password="root123",port=27149):
    """setup before test"""
    for cmd in CELLROTE:
        status = do_clicmd(host, cmd, user, password,port)
        if status == "":
            print("CELL set route sucessfull")
        else:
            print("CELL set route fail")

def setftproute():
    # set ftpserver
    ftpstatus =""
    ftpstatus = do_clicmd(ftpargs["fhost"],FTPROUTE1,"root",
                          ftpargs["fsshpw"],22)
    for i in range(32):
        i += 1
        cmd = FTPROUTE2 % (i,i)
        ftpstatus = do_clicmd(ftpargs["fhost"],cmd,"root",
                              ftpargs["fsshpw"],22)
    if ftpstatus is "":
        pirnt("FTPserver set route sucessfull")
    else:
        logger.error("FTPserver set route fail")
    return None


def initdb(uelist):
    dbfilelist = ["Database/prb.db","Database/cellrate.db",'Database/cellping.db',"Database/cellri.db","Database/load.db","Database/cellrlf.db",
                  "Database/cellues.db","Database/cpeping.db","Database/ftpping.db","Database/uerate.db","Database/ueonoff.db"]
    dbkeylist = ["cellprb","cellrate","ping","cellri","load","rlf","uecount","ping","ping","uerate","ONOFF"]
    for dbfile in dbfilelist:                        
        if os.path.exists(dbfile):
            os.remove(dbfile)
    # cell.db
    ueinfo = []
    uerate=[]
    for ue in uelist:
        ueinfo.append("Ready")
        uerate.append(["Ready","Ready"])
    dbintlist=[]
    dbintlist.append("Ready Ready")
    dbintlist.append(["Ready","Ready"])
    dbintlist.append("Ready")
    dbintlist.append("Ready,Ready")
    dbintlist.append("Ready")
    dbintlist.append("Ready")
    dbintlist.append("Ready")
    dbintlist.append(ueinfo)
    dbintlist.append(ueinfo)
    dbintlist.append(uerate)
    dbintlist.append(",".join(ueinfo))
    for key,value,dbfile in zip(dbkeylist,dbintlist,dbfilelist):
        try:
            s = shelve.open(dbfile)
            s[key] = value
            s.close()
        except:
            print "db file init fail"

def open_root_permissions(hostname="192.168.9.149",password="admin",adminpassword="qpa;10@(",
                          port=27149):
    try:
        client=paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, int(port), "root", "root123")	
        client.close()
        return
    except:
        pass
    cmd_profile = "source /etc/profile;"
    port = int(port)
    client=paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, port, "admin", password)
    stdin_read_write1,stdout_read_write1,stderr_read_write1=client.exec_command(cmd_profile)
		
    ssh = client.invoke_shell()	
    time.sleep(1)	
		
    ssh.send('admin')
    ssh.send('\n')	
    buff = ''
    while not buff.strip().endswith('passwd:'):
	resp = ssh.recv(65535)
	buff +=str(resp)
    print buff	
    ssh.send(adminpassword)
    ssh.send('\n')	
    buff = ''		
    while not buff.strip().endswith('#'):
	resp = ssh.recv(65535)
	buff +=str(resp)
    print buff
			
    ssh.send('start-shell')
    ssh.send('\n')	
    buff = ''
    while not buff.strip().endswith('$'):
	resp = ssh.recv(65535)
	buff +=str(resp)
    print buff
    
    ssh.send('sudo su root')
    ssh.send('\n')
    buff = ''
    while not buff.strip().endswith('#'):
	resp = ssh.recv(65535)
	buff +=str(resp)
    print buff
		
    ssh.send('sed -i "s/PermitRootLogin no/PermitRootLogin yes/g" /etc/ssh/sshd_config')
    ssh.send('\n')
    buff = ''
    while not buff.strip().endswith('#'):
	resp = ssh.recv(65535)
	buff +=str(resp)
    print buff
		
    ssh.send('cd /etc/init.d')
    ssh.send('\n')
    buff = ''
    while not buff.strip().endswith('#'):
	resp = ssh.recv(65535)
	buff +=str(resp)
    print buff
		
    ssh.send('./sshd restart')
    ssh.send('\n')
    buff = ''
    while not buff.strip().endswith('#'):
	resp = ssh.recv(65535)
	buff +=str(resp)
    print buff
    client.close()

def setfile():
    if not os.path.exists("Result"):
        os.mkdir("Result")
    if not os.path.exists("Database"):
        os.mkdir("Database")

