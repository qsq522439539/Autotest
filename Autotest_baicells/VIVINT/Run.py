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
import xml.dom.minidom
import logging
import mp3play
import paramiko
import zipfile
import smtplib
import shelve
import shutil

from multiprocessing import Process
from ftplib import FTP
from optparse import OptionParser
from xml.dom import  minidom


reload(sys) 
sys.setdefaultencoding('utf-8')
ISOTIMEFORMAT='%Y-%m-%d-%X'
HOMEDIR = sys.path[0]




class Parsing_XML():
    def __init__(self):
        self.logger = logging.getLogger('test')
    '''Parsing XML-formatted files for Lart_i'''
    def get_attrvalue(self,node, attrname):
        return node.getAttribute(attrname) if node else ''

    def get_nodevalue(self,node, index = 0):
        return node.childNodes[index].nodeValue if node else ''

    def get_xmlnode(self,node,name):
        return node.getElementsByTagName(name) if node else []

    def xml_to_string(self,filename):
        doc = minidom.parse(filename)
        return doc.toxml('UTF-8')

    def get_xml_data(self,filename):
        doc = minidom.parse(filename) 
        root = doc.documentElement
        ue_nodes = self.get_xmlnode(root,'ue')
        ue_list={}
        for node in ue_nodes:
            ue_id = self.get_attrvalue(node,'id') 
            node_clientip = self.get_xmlnode(node,'clientip')
            node_serverip = self.get_xmlnode(node, 'serverip')
            node_downfile = self.get_xmlnode(node,'downfile')
            node_localpath = self.get_xmlnode(node,'localpath')
            node_upfile = self.get_xmlnode(node, 'ufile')
            node_uppath = self.get_xmlnode(node, 'uppath')
            ue_clientip = self.get_nodevalue(node_clientip[0])
            ue_serverip = self.get_nodevalue(node_serverip[0])
            ue_downfile = self.get_nodevalue(node_downfile[0])
            ue_localpath = self.get_nodevalue(node_localpath[0]).encode('utf-8','ignore')
            ue_upfile = self.get_nodevalue(node_upfile[0])
            ue_uppath = self.get_nodevalue(node_uppath[0]).encode('utf-8','ignore') 
            ue = {}
            ue['clientip'] , ue['serverip'], ue['downfile'] , ue['localpath'], ue['upfile'], ue['uppath'] = (
                ue_clientip, ue_serverip, ue_downfile, ue_localpath, ue_upfile, ue_uppath)
            ue_list[ue_id] = ue
        return ue_list

    @staticmethod
    def parsing_label_list(labelname, xmlfile):
        '''Parsing Gets the list labels'''
        try:
            xml_dom = xml.dom.minidom.parse(xmlfile)
            xml_label = xml_dom.getElementsByTagName(labelname)
        except IOError:
            print ('Failed to open %s file,Please check it' % xmlfile)
        xml_label_list = []
        for single_label in xml_label:
            xml_label_list.append(single_label.firstChild.data)
        return xml_label_list

    @staticmethod
    def specific_elements(labelname, xmlfile):
        '''Read the specific elements,call the class may need to override
           this function.By default returns a "xml_list" and "xml_dict" a
           dictionary of xml_list specify a label for the list xml_dict
           key for the XML element, the corresponding value for a list of
           corresponding element tag content
        '''
        xml_labels = Parsing_XML.parsing_label_list(labelname, xmlfile)[0].split(" ")
        xml_elements_dict = {}
        for per_label in xml_labels:
            per_xml_label_list = Parsing_XML.parsing_label_list(per_label, xmlfile)
            xml_elements_dict[per_label] = per_xml_label_list[0]
        return xml_elements_dict     
    
class FtpStress(FTP):
    def __init__(self):
        self.logger = logging.getLogger('test')
    # Private
    # Private comman
    def _getnumbits(self, rateless):
        """
        function: Converts "M-K" to bit
        """
        if rateless[-1] == "M":
            return int(float(rateless[:-1])) * 1024 * 1024
        elif rateless[-1] == "K":
            return int(float(rateless[:-1])) * 1024
        else:
            return int(float(rateless))

    def _cilent_thread_exit(self, thread):
        """
         function: kill client's process
        """
        try:
            thread.kill()
            return True
        except:
            print "thread %s exit faild" % thread.pid()
            return False

    # Private
    ## FTP Test
    def ConnectFTP(self,remoteip,loginname,loginpassword):    
	ftp=FtpStress() 
	try:  
	    ftp.connect(remoteip,21,600)    
	except Exception, e:
	    self.logger.error("%s conncet failed - %s" % (remoteip,e))
	    return (0,'conncet failed')    
	else:    
	    try:    
		ftp.login(loginname,loginpassword)     
	    except Exception, e:
		self.logger.error('%s login failed - %s' % (remoteip,e))
		return (0,'login failed')    
	    else:
		return (1,ftp)    
		
    def download(self,host,username,password,remotepath,localpath):    
	#connect to the FTP Server and check the return
        try:
	    res = self.ConnectFTP(host,username,password)    
	    if(res[0]!=1):
                self.logger.error(" download ftp connect create faild")
	        return
	    ftp=res[1]
	    dires = self.splitpath(remotepath)
	except:
            self.logger.error("download  ftp connect create faild")
            return
	if dires[0]:
            try:
                ftp.set_pasv(True)
	        ftp.cwd(dires[0])   # change remote work dir
	    except:
                self.logger.error("download ftp changge dir faild")
                ftp.set_pasv(False)
        try:
	    remotefile=dires[1]     # remote file name	
	    blocksize=1024 * 1024
	    ftp.voidcmd('TYPE I')
	    conn = ftp.transfercmd('RETR ' + remotefile)
	except:
            self.logger.error("download ftp download create faild") 
            return
	#lwrite=open(localpath,'ab')
	while True:
            try:
	        data=conn.recv(blocksize)
	    except:
                self.logger.error("download ftp transfer faild")
                return "ERROR2"
	try:
	    ftp.voidcmd('NOOP')
	    ftp.voidresp()
	    conn.close()
	    ftp.quit()
	except:
            self.logger.error("ftp close faild")
            return 

    def upload(self,host,username,password,remotepath,localpath):
        try:
	    res = self.ConnectFTP(host,username,password)
	    if res[0]!=1:
                self.logger.error("upload ftp connect create faild")
	        return
	    ftp=res[1]
	    ftp.set_pasv(True)
        except:
            pass
        try:
	    remote=self.splitpath(remotepath)
	    localf=open(localpath,'rb')
	    ftp.voidcmd('TYPE I')
	    datasock=ftp.transfercmd("STOR "+remote[1])
	except:
            self.logger.error("upload  ftp connect create faild")
            return 
	while True:
            try:
	        buf=localf.read(1024 * 1024)
	        if not len(buf):
		    break
	        datasock.send(buf)
	    except:
                self.logger.error("upload ftp upload faild")
        try:
	    datasock.close()
	    localf.close()
	    ftp.voidcmd('NOOP')
	    ftp.voidresp()
	    ftp.quit()
	    return
 	except:
            self.logger.error("upload ftp close faild")
    
    def splitpath(self,remotepath):
        try:
	    position=remotepath.rfind('/')
	    return (remotepath[:position+1],remotepath[position+1:])
	except:
            return
 
    def _ping(self, ip):
        REPATH = re.compile(r'\xca\xb1\xbc\xe4=(.*?)ms')
        REPATH1 = re.compile(r'\xca\xb1\xbc\xe4<(.*?)ms')
        cmd = "ping %s -n 1 " %(ip)
        result = ""
        self.logger.info("start ping")
        try:
            p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            p.wait()
            buff = p.stdout.read()
            result1 = REPATH.findall(buff)
            result2 = REPATH1.findall(buff)
            if len(result1) > 0:
                result = result1[0]
            if len(result2) >0:
                result = result2[0]
            if len(result1) < 0 and len(result2) < 0:
                result = "Fail"
        except:
            result = "Fail"
            self.logger.error("ping server is fail")
        print result
        try:
            f = open("Result/Result.csv",'a')
            f.write("%s,,,%s\n" % (time.strftime('%Y:%m:%d:%H:%M:%S'),result))
            f.close()
        except:
            pass
        return

    def dogetrate(self,hostname,username, password, port):
        ulcmd = "grep dlTtlTpt /tmp/log/syslog | tail -n 1 | awk -F ' ' '{print $5}' | tr -d '\nulTtlTpt='"
        dlcmd = "grep dlTtlTpt /tmp/log/syslog | tail -n 1 | awk -F ' ' '{print $7}' | tr -d '\ndlTtlTpt='"
        cmd = "grep dlTtlTpt /tmp/log/syslog | tail -n 1 | awk -F ' ' '{print $5,$7}' | tr -d '\ndulTtlTpt='"
        try:
            client=paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(hostname, port, username, password)	
            stdin,stdout,stderr=client.exec_command(cmd)
            rate=stdout.read()
            client.close()
            if rate == "":
                return "NULL"
            else:
                return rate
        except:
            print "get rate fail"
            return "NULL"
            
    # Save syslog rate 
    def syslog_save_rate(self,hostname,username, password, port):
        port = int(port)
        time.sleep(10)
        logfile="Result/Result.csv"
        for i in range(2):
            status = self.dogetrate(hostname,username, password, port)
            if status == "NULL":
                self.logger.error("rate get faild")
            else:
                status = status.split(" ")
                try:
                    f = open(logfile, 'a')
                    f.write('%s,%s,%s, \n' % (time.strftime('%Y:%m:%d:%H:%M:%S'),status[0],status[1]))
                    f.close()
                except:
                    pass
            time.sleep(20)
        return
    
        # FTP stress
    def Ftp_Stresstest_down(self,inputargs, ftpargs, ueargs):
        loadthreads = []
        # create test thread
        for i in range(int(inputargs["download"])):
            downthread = threading.Thread(target=self.download,
                                          name="downloadftp%s"%i,
                                          args=(ueargs["001"]["serverip"],
                                                ftpargs["ftpuser"],
                                                ftpargs["ftppw"],
                                                ueargs["001"]["downfile"],
                                                ueargs["001"]["localpath"]))
            loadthreads.append(downthread)
        ratethread = threading.Thread(target=self.syslog_save_rate,
                                   name="ratecheck",
                                   args=("192.168.9.79",
                                         "root","baicells",22))
        ratethread.setDaemon(True)
        for n,thread in enumerate(loadthreads):
            thread.setDaemon(True)
            thread.start()
            self.logger.info("The %s  download thread start" % n)
        ratethread.start()
        time.sleep(60)
        self.logger.info("Ftp down test finsish")
        return

    def Ftp_Stresstest_up(self,inputargs, ftpargs, ueargs):
        testtime = int(inputargs["testtime"])
        loadthreads = []
        # create test thread
        for i in range(int(inputargs["upload"])):
            upfile= ueargs["001"]["upfile"] + str(i)
            uppath = ueargs["001"]["uppath"] + str(i)
            upthread = threading.Thread(target=self.upload,
                                        name="uploadftp%s"%i,
                                        args=(ueargs["001"]["serverip"],
                                              ftpargs["ftpuser"],
                                              ftpargs["ftppw"],
                                              upfile,
                                              uppath))
            loadthreads.append(upthread)
        ratethread = threading.Thread(target=self.syslog_save_rate,
                                      name="ratecheck",
                                      args=("192.168.9.79",
                                         "root","baicells",22))
        ratethread.setDaemon(True)
        for n,thread in enumerate(loadthreads):
            thread.setDaemon(True)
            thread.start()
            self.logger.info("The %s upload thread start" % n)
        ratethread.start()
        time.sleep(60)
        self.logger.info("Ftp  up test finsish")
        return 

    def Run_Ftp_Test(self,reciveargs, ftpargs, ueargs):
        try:
            f = open("Result/Result.csv", 'a')
            f.write('Time,UL,DL,Ping(ms)\n')
            f.close()
        except:
            pass
        testtime = int(reciveargs["testtime"])
        loadthreads = []
        starttime = time.time()
        # create test thread
        while time.time() - starttime < testtime:
            self._ping(ueargs["001"]["serverip"])
            # do down load test
            self.Ftp_Stresstest_down(reciveargs,ftpargs,ueargs)
            self._ping(ueargs["001"]["serverip"])
            # do up load test
            self.Ftp_Stresstest_up(reciveargs,ftpargs,ueargs)
            time.sleep(30)
        print "test finished"
        return  
    
    
def recive_args():
    parser = OptionParser()
    parser.add_option("-d", "--dl", dest="download",
                      help="Number of downlink transfer UE.\
                            default=1.")
    parser.add_option("-u", "--ul", dest="upload",
                     help="Number of downlink transfer UE.\
                            default=0.")
    parser.add_option("-t", "--num", dest="testtime",
                      help="Test seconds.\
                            default:600.")
    (options, args) = parser.parse_args()
    test_args = {}
    if options.download is None:
        options.download = "1"
    if options.upload is None:
        options.upload = "1"
    if options.testtime is None:
        options.testtime = "90"
    test_args["download"] = options.download
    test_args["upload"] = options.upload
    test_args["testtime"] = options.testtime
    return test_args

def setloger():
    logger = logging.getLogger('test')
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler('Result/testlog.txt')
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)
    formatter = logging.Formatter('%(asctime)s - %(name)s -%(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)

def do_clicmd(hostname, command, username="root", password="root123",
              port="27149"):
    '''
    Set the basic configuration in cli.txt.	
    hostname: the conneced host IP address		
    username: login host name		
    password: login host password	
    path: storage path of the configuration script and log
    '''
    port = int(port)	
    client=paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, port, username, password)	
    stdin,stdout,stderr=client.exec_command("%s" % command)
    returncode=stdout.read()
    client.close()
    return returncode
    
if __name__ == "__main__":
    if not os.path.exists("Result"):
        os.mkdir("Result")
    if os.path.exists("Result/testlog.txt"):
        os.remove("Result/testlog.txt")
    if os.path.exists("Result/Result.csv"):
        os.remove("Result/Result.csv")
    setloger()
    reciveargs =  recive_args()
    logger = logging.getLogger('test')
    ftpargs = Parsing_XML.specific_elements('comonlabel', 'args.xml')
    logger.info("Ftp args is %s " % ftpargs)
    parxml= Parsing_XML()
    ueargs= parxml.get_xml_data('args.xml')
    logger.info("UE args is %s " % ueargs)
    logger.info("Ftp setting start")
    dolist = ftpargs["dotest"].split(" ")
    logger.info("Ftp test is start")
    test = FtpStress()
    test.Run_Ftp_Test(reciveargs,ftpargs,ueargs)
