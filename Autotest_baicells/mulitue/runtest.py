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
import mp3play
import paramiko
import shelve

from PyQt4.Qt import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import QtGui, QtCore

from multiprocessing import Process
from ftplib import FTP
from optparse import OptionParser
from xml.dom import  minidom

from monitor import *


reload(sys) 
sys.setdefaultencoding('utf-8')


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
	try:
            ftp=FtpStress()
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
		
    def download(self,starttime,testtime,host,username,password,remotepath,localpath):    
	#connect to the FTP Server and check the return
        try:
	    res = self.ConnectFTP(host,username,password)    
	    if(res[0]!=1):
	        return "ERROR1"	 
	    ftp=res[1]
	    dires = self.splitpath(remotepath)
	except:
            return
	if dires[0]:
            try:
                ftp.set_pasv(True)
	        ftp.cwd(dires[0])   # change remote work dir
	    except:
                ftp.set_pasv(False)
                pass
        try:
	    remotefile=dires[1]     # remote file name	
	    blocksize=1024 * 1024
	    ftp.voidcmd('TYPE I')
	    conn = ftp.transfercmd('RETR ' + remotefile)
	except:
            return "ERROR2"
	#lwrite=open(localpath,'ab')
	while True:
            try:
                if time.time() - starttime < testtime:
	            data=conn.recv(blocksize)
	    except:
                return "ERROR2"
	    if not data:
		break 
	    #lwrite.write(data)
	#lwrite.close()
	try:
	    ftp.voidcmd('NOOP')
	    ftp.voidresp()
	    conn.close()
	    ftp.quit()
	except:
            return "ERROR2"

    def upload(self,starttime,testtime,host,username,password,remotepath,localpath):
        try:
	    res = self.ConnectFTP(host,username,password)
	    if res[0]!=1:
	        return "ERROR1"
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
            return "ERROR2"
	while True:
            try:
                if time.time() - starttime < testtime:
	            buf=localf.read(1024 * 1024)
	            if not len(buf):
		        break
	            datasock.send(buf)
	    except:
                return "ERROR3"
        try:
	    datasock.close()
	    localf.close()
	    ftp.voidcmd('NOOP')
	    ftp.voidresp()
	    ftp.quit()
	    return "ERROR3"
 	except:
            return 
    
    def splitpath(self,remotepath):
        try:
	    position=remotepath.rfind('/')
	    return (remotepath[:position+1],remotepath[position+1:])
	except:
            return

    def repair(self,host):
        try:
            for cmd in CELLROTE:
                status = do_clicmd(host, cmd)
                if status == None or status == "pass":
                    self.logger.info("CELL set route sucessfull")
                else:
                    self.logger.error("%s CELL set route fail" % host)
            return
        except:
            return

    def _Download_FTP(self,chost,testtime, remotepath,localpath,
                      host, username, password):
	'''
	FTP service.
	host: the conneced host IP address
	username: login host name
	password: login host password
	remotepath: storage path of download file
	localpath： local path of saved file
	'''
	testtime=int(testtime)
	starttime = time.time()
	self.logger.info("%s start down load time on %s" %(host,starttime))
	while True:
            if time.time() - starttime > testtime:
                break
            #status = self._downftp(starttime,testtime,host,username,password,remotepath,localpath)
            status = self.download(starttime,testtime,host,username,password,remotepath,localpath)
            if status is "ERROR1":
                self.logger.error("%s ftp connect failed" % host)
                #self.sendalert(alert,"ftperror", host)
                time.sleep(60)
                self.repair(chost)
            elif status is "ERROR2":
                self.logger.info("%s ftp download Interrupt" % host)
               # self.sendalert(alert,"dlerror", host)
                time.sleep(60)
                self.repair(chost)
	return True

    def _Upload_FTP(self,chost,testtime, remotepath,localpath,
                    host, username, password):
	'''
	FTP upload service.	
	host: the conneced host IP address	
	username: login host name
	password: login host password
	remotepath: storage path of download file
	localpath： local path of saved file
	'''
	self.endsigle = True
	if not os.path.exists(localpath):
	    self.logger.error("%s file doesn't exists" % localpath)
	    return False
	starttime = time.time()
	self.logger.info("%s start up load on %s" %(host,starttime))
	teststatus = []
	while True:
            timenow = time.time()
            if timenow - starttime > testtime:
                break
            status = self.upload(starttime,testtime,host,username,password,remotepath,
               localpath)
            if status is "ERROR1":
                self.logger.error("%s ftp connect failed" %host )
               # self.sendalert(alert,"ftperror", host)
                self.repair(chost)
                time.sleep(60)
            elif status is "ERROR2":
                self.logger.error("%s ftp start error"%host)
             #   self.sendalert(alert,"ulerror", host)
                self.repair(chost)
                time.sleep(60)
            elif status is "ERROR3":
                self.logger.error("%s ftp upload Interrupt" %host)
              #  self.sendalert(alert,"ulerror", host)
                self.repair(chost)
                time.sleep(60)          
	return True
    
        # FTP stress
    def Ftp_Stresstest(self,imsilist,argstemp,DLUL,inputargs,ftpargs,
                       ueargs,cpeiplist,ftpiplist):
        doullist=[]
        dodllist=[]
        for index in argstemp:
            if DLUL[index] == "DL":
                dodllist.append(index)
            else:
                doullist.append(index)
        testtime = int(inputargs["testtime"])
        ftpuser=ftpargs["ftpuser"]
        ftppw = ftpargs["ftppw"]
        # test thread
        # do download
        downloadthreads = []
        uploadthreads = []
        cellport = int(ftpargs["cport"])
        for num in dodllist:
            downthread = threading.Thread(target=self._Download_FTP,
                                          name="downloadftp",
                                          args=(ftpargs["chost"],
                                                testtime,
                                                ueargs[num]["downfile"],
                                                ueargs[num]["localpath"],
                                                ueargs[num]["serverip"],
                                                ftpuser,ftppw))
            downloadthreads.append(downthread)
            downthread.setDaemon(True)
            downthread.start()
        #    self.logger.info("%s is start download" % imsilist[num])
        for num in doullist:
            upthread = threading.Thread(target=self._Upload_FTP,
                                        name = "uploadftp",
                                        args=(ftpargs["chost"],
                                              testtime,
                                              ueargs[num]["upfile"],
                                              ueargs[num]["uppath"],
                                              ueargs[num]["serverip"],
                                              ftpuser,ftppw))
            uploadthreads.append(upthread)
            upthread.setDaemon(True)
            upthread.start()
         #   self.loger.info("%s is start upload" % imsilist[num])
        dotestthread = downloadthreads + uploadthreads
        for thread in dotestthread:
            thread.join()
        #self.sendalert(inputargs["alarm"],"Result")
       # logger.info("Ftp test finsish")
        return    

class TestWindow(QDialog):

    def __init__(self,cpeiplist,ftpiplist,celllist,ftpargs, ueargs):
        QDialog.__init__(self) 
        self.celllist = celllist
        self.argstemp = []
        self.dolist = []
        self.cellip = ftpargs['chost']
        self.cpeiplist = cpeiplist
        self.ftpiplist = ftpiplist
        self.ftpargs = ftpargs
        self.ueargs = ueargs
        self.setWindowTitle(u"业务测试启动")
        palette1 = QtGui.QPalette()
        palette1.setColor(self.backgroundRole(), QColor("#5F9EA0"))
        self.setPalette(palette1)
        self.setAutoFillBackground(True)
        self.createlabel()
        self.createcheckbox()
        self.createbutton()
        self.Layout()

    def createlabel(self):
        self.titlelabel = QLabel(u"UE 列表")
        self.argslabel = QLabel(u"参数设置")
        self.label_0 = QLabel(self.tr(u"UL Threads"))
        self.label_1 = QLabel(self.tr(u"DL Threads"))
        self.label_2 = QLabel(self.tr(u"Test Time(sec)"))
        self.edit0 = QtGui.QLineEdit()
        self.edit1 = QtGui.QLineEdit()
        self.edit2 = QtGui.QLineEdit()
        self.edit2.setText('9999')

    def createcheckbox(self):
        self.cellbox = []
        self.combox = []
        num_ = 0
        self.DLUL = []
        for cell in self.celllist:
            self.combol = QtGui.QComboBox()
            self.combol.addItem("DL")
            self.combol.addItem("UL")
            self.combol.value = num_
            self.combol.activated.connect(self.change)
            self.combox.append(self.combol)
            num_+=1
        for box in self.combox:
            self.DLUL.append("DL")
        id_ = 0
        for cell in self.celllist:
            self.checkbox = QtGui.QCheckBox(u'%s' % cell)
            self.checkbox.value = id_
            self.checkbox.cell = cell
            self.checkbox.stateChanged.connect(self.checks)
            self.cellbox.append(self.checkbox)
            id_ += 1

    def change(self,start):
        combox = self.sender()
        if self.DLUL[combox.value] == "DL":
            self.DLUL[combox.value] = "UL"
        else:
            self.DLUL[combox.value] = "DL"

    def checks(self,start):
        checkbox=self.sender()#获取发射信号对象
        if start==Qt.Checked:
            self.dolist.append(checkbox.cell)
            self.argstemp.append(checkbox.value)
        elif start==Qt.Unchecked:
            try:
                self.argstemp.remove(checkbox.value)
                self.dolist.remove(checkbox.cell)
            except:
                pass

    def createbutton(self):
        self.defaultbutton = QtGui.QPushButton(u"帮助")
        self.connect(self.defaultbutton, QtCore.SIGNAL('clicked()'),
                     self.Ondefault)
        self.helpbutton = QtGui.QPushButton(u"状态监控")
        self.connect(self.helpbutton, QtCore.SIGNAL('clicked()'),
                     self.Onhelp)
        self.setbutton = QtGui.QPushButton(u"启动测试")
        self.connect(self.setbutton, QtCore.SIGNAL('clicked()'),
                     self.Onstart)
        self.setallbutton = QtGui.QPushButton(u"全选")
        self.connect(self.setallbutton, QtCore.SIGNAL('clicked()'),
                     self.Onsetall)
    
    def Layout(self):
        baseLayout = QGridLayout()
        baseLayout.addWidget(self.titlelabel, 0,0)
        i = 1
        j = 0
        for n,cell in enumerate(self.cellbox):
            baseLayout.addWidget(cell,i,j)
            baseLayout.addWidget(self.combox[n],i,j+1)
            j+=2
            if j == 10:
                j = 0
                i += 1
                
        baseLayout.addWidget(self.argslabel, i+1,0)
        #baseLayout.addWidget(self.label_0, i+2,0)
       # baseLayout.addWidget(self.label_1, i+3,0)
        baseLayout.addWidget(self.label_2, i+2,0)
       # baseLayout.addWidget(self.edit0, i+2,1)
       # baseLayout.addWidget(self.edit1, i+3,1)
        baseLayout.addWidget(self.edit2, i+2,1)
        
        footer1Layout = QHBoxLayout()
        acer1 = QtGui.QSpacerItem(50,30)
        acer2 = QtGui.QSpacerItem(50,10)

        footer2Layout = QHBoxLayout()
        footer1Layout.addWidget(self.helpbutton)
        footer1Layout.addWidget(self.defaultbutton)
        # baseLayout.addItem(acer1, i+5,0)
        # baseLayout.addItem(acer2, i+5,1)
        footer2Layout.addWidget(self.setallbutton)
        footer2Layout.addWidget(self.setbutton)

        baseLayout.setSizeConstraint(QLayout.SetFixedSize)
        baseLayout.setSpacing(10)
        baseLayout.addLayout(footer1Layout,i+5,0)
        baseLayout.addLayout(footer2Layout,i+5,3)
        self.setLayout(baseLayout)

    def Ondefault(self):
        QtGui.QMessageBox.about(self, u'关于MultiUe',u"MuliteUe是进行多UE业务测试的工具。\n\n\
本工具支持以下功能：\n\
  1．支持多UE(最多达96UE)FTP上传/下载业务测试；\n\
  2．支持测试时长设定;\n\
  3. 支持测试过程因异常业务中断后的自动恢复;\n\
  4．支持定制UE扩展和定制；\n\
  5．支持多种指标的状态监控；\n\
  6. 支持业务测试和监控的独立运行;\n\n\n\n\
本工具使用权属于：北京佰才邦技术有限公司\n\
Copyright (c) Baicells Technologies Co. Ltd.")

    def Onhelp(self):
        self.checkwin.show()
        
    def Onstart(self):
        inputargs = {}
        inputargs["testtime"] = self.edit2.text()
        inputargs["alarm"] = "A"
        self.dotest = TestThread(self.celllist,self.argstemp,self.DLUL,inputargs,
                            self.ftpargs,self.ueargs,self.cpeiplist,self.ftpiplist)
        self.dotest.start()
        self.setbutton.setText(u"测试中")
        
    def Onsetall(self):
        for check in self.cellbox[0:32]:
            check.setChecked(True)

   
class MainWindow(QtGui.QMainWindow):  
    def __init__(self,cpeiplist,ftpiplist,celllist,ftpargs, ueargs):
        self.celllist = celllist
        self.cellip = ftpargs['chost']
        self.cpeiplist = cpeiplist
        self.ftpiplist = ftpiplist
        self.ftpargs = ftpargs
        self.ueargs = ueargs
        QtGui.QMainWindow.__init__(self)  

        self.setWindowTitle(u"Baicells业务测试工具")
        palette1 = QtGui.QPalette()
        palette1.setColor(self.backgroundRole(), QColor("#D8BFD8"))
        tabs = QtGui.QTabWidget(self)  
        self.tab1 = TestWindow(self.cpeiplist,self.ftpiplist,self.celllist,self.ftpargs, self.ueargs)
        #tab2  
        self.tab2 = SetMonitor(self.cpeiplist,self.ftpiplist,self.celllist,self.ftpargs, self.ueargs)
        
          
        tabs.addTab(self.tab1,u"测试设置")  
        tabs.addTab(self.tab2,u"监控设置")  
        #sconsole.resize(900,750)
        tabs.resize(1190, 750)
        self.tab2.resize(1200, 750)
        self.resize(1132, 736)
       # desktop = QtGui.QApplication.desktop()
        #rect = desktop.availableGeometry()
        #self.setGeometry(rect)
        
        #禁止最大化  
        self.setWindowFlags(QtCore.Qt.WindowMinimizeButtonHint)
        self.setFixedSize(self.width(), self.height());   
        self.show()  
          

class TestThread(QThread):

    def __init__(self,uelist,argstemp,DLUL,inputargs,ftpargs,
                 ueargs,cpeiplist,ftpiplist):
        QThread.__init__(self)
        self.argstemp = argstemp
        self.inputargs = inputargs
        self.ftpargs = ftpargs
        self.ueargs = ueargs
        self.DLUL = DLUL
        self.uelist = uelist
        self.cpeiplist = cpeiplist
        self.ftpiplist = ftpiplist
        
    def run(self):
        testjob = FtpStress()
        testjob.Ftp_Stresstest(self.uelist,self.argstemp,self.DLUL,self.inputargs,
                               self.ftpargs,self.ueargs,self.cpeiplist,self.ftpiplist)        

