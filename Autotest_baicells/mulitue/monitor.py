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
import smtplib
import shelve

from PyQt4.Qt import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import QtGui, QtCore
from multiprocessing import Process
from optparse import OptionParser

reload(sys) 
sys.setdefaultencoding('utf-8')


class DoAlert:
    def _playmp3(self,mfile):
        clip = mp3play.load(mfile)
        clip.play()
        logger.info("Play music")
        time.sleep(min(30, clip.seconds()))
        clip.stop()
        return 

    def sendalert(self,alarttype,error,host="",mfile="123.mp3"):
       if alarttype is "V":
           pass
          # music = threading.Thread(target=self._playmp3,name="music",args=("123.mp3",))
          # music.start()
       elif alarttype is "M":
           mail = threading.Thread(target=self.send_mail,name="mail",args=(host,error))
           mail.start()
       elif alarttype is "A":
          # music = threading.Thread(target=self._playmp3,name="music",args=("123.mp3",))
          # music.start()
           mail = threading.Thread(target=self.send_mail,name="mail",args=(host,error))
           mail.start()

    def makezip(self,resultfile,srcdirectory):
        f = zipfile.ZipFile(resultfile,'w',zipfile.ZIP_DEFLATED)    
        for dirpath, dirnames, filenames in os.walk(srcdirectory):  
	    for filename in filenames:  
	        f.write(os.path.join(dirpath,filename))  
        f.close() 
    
    def automail_result(self,host,filename,error):
        cur_time=time.strftime(ISOTIMEFORMAT,time.localtime(time.time()))
        message={
            "pingerror": "ue is ping faild",
            "ratelow": "Total rate is bellow than expectd",
            "Result": "FTP test Result",
            "ftperror": "ftp connect failed",
            "dlerror": "ftp download Interrupt",
            "ulerror": "ftp upload Interrupt"}
        if error is "pingerror" or "ftperror" or "dlerror" or "ulerror":
            title = "%s %s (%s)" % (host, message[error], cur_time)
        elif error is "ratelow":
            title = "%s (%s)" % (message[error], cur_time)
        elif error is "Result":
            title = "%s" % message[error] 

        msg = MIMEMultipart()
        text='''
Hi!
   %s
   Attachment is the test results , sent automatically by the FTPtest.

Please check it.

------- You are receiving this mail because: -------

You are in the mail list of the FTPtest .

Do not reply to this message.

Because this message is automatically sent by FTPtest.

Thanks.

FTPtest
''' % message[error]

        part1 = MIMEText(text,'plain')
        msg.attach(part1)
        part=MIMEBase('application','octet-stream')
        part.set_payload(open('%s'%filename, 'rb').read())
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename=%s'%filename.split("/")[-1])
        msg.attach(part)

        msg['from'] = 'autotest@baicells.com'
        msg['subject'] = '%s %s (%s)' %(host,message[error],cur_time)
        try:
            server = smtplib.SMTP()
            server.connect('smtp.baicells.com')
            server.login('autotest@baicells.com','123456a!')
            server.sendmail(msg['from'], MAILIST, msg.as_string())
            server.quit()
        except Exception, errormessage:  
            print str(errormessage)

    def send_mail(self,host,error):
        resultfile = "tmp/" + str(time.time()) + '.zip'
        self.makezip(resultfile,"Result") 
        self.automail_result(host,resultfile,error)
        logger.info("mail send ok")
        return
    
    
class DoMonitor:
    def __init__(self):
        self.logger = logging.getLogger('test')
        
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

    # write file
    def _write_file(self,filename,writeinfo):
        try:
            f = open(filename,'a')
            f.write(writeinfo)
            f.close()
        except:
            pass

    # write dbfile
    def _write_database(self,dbfile,key,value):
        try:
            s = shelve.open(dbfile)
            s[key] = value
            s.close()
        except:
            pass

    # do ssh cmd
    def cell_ssh_cmd(self,cmd,hostname,username,password,port):
        try:
            client=paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(hostname, port, username, password)	
            stdin,stdout,stderr=client.exec_command(cmd)
            returninfo=stdout.read()
            client.close()
            return returninfo
        except:
            return None

    def dogetrate(self,hostname,username, password, port):
        cmd = "grep dlTtlTpt /tmp/log/syslog | awk -F ' ' '{print $7,$9}' | tr -d 'ulTtlTpt=dlTtlTpt=' | tail -n 1 | tr -d '\n'"
        rate=self.cell_ssh_cmd(cmd,hostname,username,password,port)
        if rate == None:
            return ["None","None"]
        elif rate == "":
            return ["NULL","NULL"]
        else:
            rate = rate.split(' ')
            return rate
            
    # Save syslog rate 
    def syslog_save_rate(self,hostname,username, password, port):
        time.sleep(5)
        logfile="Result/cellrate.csv"
        self._write_file(logfile,'Time, UL_Rate, DL_Rate\n')
        while True:
            status = self.dogetrate(hostname,username, password, port)
            self._write_file(logfile,'%s, %s, %s\n' % (time.strftime('%Y:%m:%d:%H:%M:%S'),status[0], status[1]))
            self._write_database("Database/cellrate.db","cellrate",status)  
            time.sleep(15)
        return 
        
    def dogetvalue(self,hostname,username, password, port):
        cmd = "cli -c 'oam.getwild LTE_UE_SPEED_STATISTICS' | awk '{print $2}' | tr -d '\n[]'"
        try:
            rate=self.cell_ssh_cmd(cmd,hostname,username,password,port)
            if rate is not "":
                if rate == "NULL":
                    return "NULL"
                else:
                    list1=rate.split(";")
                    return list1
        except:
            return None

    # uestatus-ue rate save
    def _uerate_save(self,timenow,logfile,ueinfodict,uelist):
        ratelist = []
        print ueinfodict
        for ue in uelist:
            if ueinfodict == "NULL":
                ratelist.append(["NULL","NULL"])
            elif ueinfodict == "None":
                ratelist.append(["None","None"])
            else:
                if ue in ueinfodict.keys():
                    ratelist.append(ueinfodict[ue][1:3])
                else:
                    ratelist.append(["NULL","NULL"])
        print ratelist
        for uerate in ratelist:
            self._write_file(logfile,'%s,DL,%s'%(timenow,uerate[0]))
            self._write_file(logfile,'%s,UL,%s'%(timenow,uerate[1]))
        self._write_database("Database/uerate.db","uerate",ratelist)

    # uestatus bler save
    def _uebler_save(self,ueinfodict,uelist):
        pass

    # uestatus mcs save
    def _uemcs_save(self,ueinfodict,uelist):
        pass

    # uestatus-cell bler save
    def _cellbler_save(self,timenow,logfile,ueinfodict,uelist):
        pass

    # uestatus on/off
    def _ueonoff_save(self,timenow,logfile,ueinfodict,uelist):
        ueinfolist = []
        for ue in uelist:
            if ueinfodict == "NULL":
                ueinfolist.append("NULL")
            elif ueinfodict == "None":
                ueinfolist.append("None")
            else:
                if ue in ueinfodict.keys():
                    ueinfolist.append("ON")
                else:
                    ueinfolist.append("OFF")
        ueoninfo = ",".join(ueinfolist)
        ueinfo = timenow + ',' + ueoninfo + '/n'
        self._write_file(logfile,ueinfo)
        self._write_database("Database/ueonoff.db","ONOFF",ueoninfo)
    
    # check_uestatus
    def check_uestatus(self,savetype,uelist,hostname,username, password, port):
        time.sleep(5)
        # uestatus log init 
        logfilename = "Result/uestatus.log"
        self._write_file(logfilename,'Time:uestatusinfo\n')
        # ueon/off log init           
        ueonlogfile = "Result/ueatach.csv"
        uetitle = ""
        for ue in uelist:
            uetitle = uetitle + ue + ','
        ueontitle = "TIME,%s" % uetitle
        self._write_file(ueonlogfile,ueontitle)
        # uerate log init
        ueratefile = "Result/uerate.csv"
        ueratetitle ="TIME,UL/DL,%s" % uetitle
        self._write_file(ueratefile,ueratetitle)
        # cellbler init
        cellblerfile = "Result/cellbler.csv"
        while True:
            timenow = time.strftime('%Y:%m:%d:%H:%M:%S')
            message = self.dogetvalue(hostname,username, password, port)
            if message != None and message != "NULL":
                # save ue log
                messages = "%s:%s"%(timenow,message)
                self._write_file(logfilename,'%s\n'%messages)
                statuslist = []
                for ue in message:
                    statuslist.append(ue.split(":"))
                if len(statuslist[-1]) < 5:
                     uestatuslist = statuslist[:-1]
                     cellstatus = statuslist[-1]
                else:
                     uestatuslist = statuslist
                     cellstatus = ["NULL","NULL","NULL","NULL"]
                ueinfodict = {}
                for ue in uestatuslist:
                    ueinfodict[ue[0][2:]] = ue[1:]
            elif message == "NULL":
                uestatuslist = "NULL"
                cellstatus = "NULL"
            elif message == None:
                uestatuslist = "None"
                cellstatus = "None"    
            # cellbler
            if "CELLBLER_V" in savetype:
                self._cellbler_save(timenow,cellblerfile,ueinfodict,uelist)
            # uestatus on/off
            if "UEON_V" in savetype:
                self._ueonoff_save(timenow,ueonlogfile,ueinfodict,uelist)
            # uestatus mcs
            if "UEMCS_V" in savetype:
                self._uemcs_save(ueinfodict,uelist)
            # uestatus bler
            if "UEBLER_V" in savetype:
                self._uebler_save(ueinfodict,uelist)
            # uestatus rate
            if "UERATE_V" in savetype:
                self._uerate_save(timenow,ueratefile,ueinfodict,uelist)

    # check cpu load
    def getcpuload(self,hostname,username, password, port):
        cmd = "uptime | awk -F age: '{print $2}' | awk -F, '{print $1}' | tr -d ' \n'"
        load=self.cell_ssh_cmd(cmd,hostname,username,password,port)
        if load == None:
            return 0
        else:
            return load
        
    def cell_check_load(self,hostname,username, password, port):
        starttime = time.time()
        logfile = "Result/cpuload.csv"
        self._write_file(logfile,'Cell, Time, Cpuload\n')
        while True:
            load = self.getcpuload(hostname,username,password, port)
            self._write_file(logfile,'%s,%s, %s\n'%(hostname,time.strftime('%Y:%m:%d:%H:%M:%S',
                                                                           time.localtime(time.time())),load))
            self._write_database("Database/load.db","load",load)
            time.sleep(60)
        return 

    # check cell RI
    def cell_check_ri(self,hostname,username,password,port):
        loadfile = "Result/cellri.csv"
        self._write_file(loadfile,'Time, RI_1, RI_2\n')
        cmd = "grep RI /tmp/log/syslog | tail -n 1 | awk -F' ' '{print $9 \":\" $10}' | awk -F: '{print $2\",\"$4}' | tr -d '\n()'"
        while True:
            ri = self.cell_ssh_cmd(cmd,hostname,username,password,port)
            if ri == None:
                ri = "None,None"
            self._write_file(loadfile,'%s, %s\n'%(time.strftime('%Y:%m:%d:%H:%M:%S',
                                                                time.localtime(time.time())),ri))
            self._write_database("Database/cellri.db","cellri",ri)
            time.sleep(30)
        return
        
    # check cell rlf
    def _get_dbg_logfile(self,hostname,username,password,port):
        cmd = "ls dbglog* | sort | tail -n 1 | tr -d '\n'"
        dbglogfile = self.cell_ssh_cmd(cmd,hostname,username,password,port)
        if dbglogfile is not None and dbglogfile is not "":
            return dbglogfile
        else:
            return None

    def _get_dbg_linenum(self,filename,hostname,username,password,port):
        cmd = "grep RLF %s | wc -l | tr -d '\n'" %filename
        linenum = self.cell_ssh_cmd(cmd,hostname,username,password,port)
        if linenum is not None and linenum is not "":
            return linenum
        else:
            return 0
                
    def cell_check_rlf(self,hostname,username,password,port):
        logfile = "Result/cellrlf.csv"
        self._write_file(logfile,'RLF Message\n')
        cmd = "grep RLF %s | awk 'NR > %s {print}'"
        REPATH = re.compile(r'RLF')
        logfile = self._get_dbg_logfile(hostname,username,password,port)
        linenum = self._get_dbg_linenum(logfile,hostname,username,password,port)
        totallinenum = 0
        while True:
            logfilenew = self._get_dbg_logfile(hostname,username,password,port)
            if logfilenew is not None and logfilenew is not logfile:
                logfile = logfilenew
                linenum = 0
            cmd = cmd % (logfile,linenum)
            errormessage = self.cell_ssh_cmd(cmd,hostname,username,password,port)
            if errormessage is not None and errormessage is not "":
                linelist = REPATH.findall(errormessage)
                subnum = len(linelist)
                linenum = int(linenum) + subnum
                self._write_file(logfile,errormessage)
            totallinenum += int(linenum)
            self._write_database("Database/cellrlf.db","rlf",totallinenum)
            time.sleep(600)
        return

    # cellues check
    def cell_check_ues(self,hostname,username,password,port):
        logfile = "Result/cellues.csv"
        self._write_file(logfile,'Time, UEs\n')
        cmd = "cli -c 'oam.getwild UE_COUNT' | awk -F' ' '{print $2}' | tr -d '\n'"
        while True:
            uecounts = self.cell_ssh_cmd(cmd,hostname,username,password,port)
            if uecounts is not None:
                self._write_file(logfile,'%s, %s\n' % (time.strftime('%Y:%m:%d:%H:%M:%S',
                                                                     time.localtime(time.time())),uecounts))
                self._write_database("Database/cellues.db","uecount",uecounts)
            time.sleep(60)
        return

    # cellprb check
    def cell_check_prb(self,hostname,username,password,port):
        logfile = "Result/cellprb.csv"
        self._write_file(logfile,'Time,DL,UL\n')
        cmd = "grep PrbUsage /tmp/log/syslog | tail -n 1 | awk -F ' ' '{print $11,$15}' | tr -d 'PrbUsage:\n'"
        while True:
            prb = self.cell_ssh_cmd(cmd,hostname,username,password,port)
            if prb is not None and prb is not "":
                prblist=prb.split(' ')
            else:
                prblist=["0.00","0.00"]
                prb="0.00 0.00"
            self._write_file(logfile,'%s, %s, %s\n' % (time.strftime('%Y:%m:%d:%H:%M:%S',
                                                                     time.localtime(time.time())),prblist[0],prblist[1]))
            self._write_database("Database/cellprb.db","cellprb",prb)
            time.sleep(30)
        return      
        
    def _pinglist_check(self,iplist,key,dbfile):
        while True:
            pinglist = []
            for ip in iplist:
                status = self._ping(ip)
                if status:
                    self.logger.info("%s is ping ok" % ip)
                    pinglist.append("Pass")
                else:
                    self.logger.error("%s is ping fail" % ip)
                    pinglist.append("Fail")
            try:
                s = shelve.open(dbfile)
                s[key] = pinglist
                s.close()
            except:
                 pass
            ipnum = len(iplist)
            time.sleep(3*ipnum)

    def _ping_check(self,ip,dbfile):
        while True:
            status = self._ping(ip)
            try:
                s = shelve.open(dbfile)
                if status:
                    self.logger.info("%s is ping ok" % ip)
                    s["ping"] = "PASS"
                else:
                    self.logger.error("%s is ping fail" % ip)
                    s["ping"] = "FAIL"
                s.close()
            except:
                pass
            time.sleep(10)

    def _ping(self, ip):
        REPATH = re.compile(r'TTL')
        cmd = "ping %s -n 3" % ip
        try:
            p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            while p.poll() is None:
                buff = p.stdout.readline()
                if REPATH.findall(buff):
                    return True
            return False 
        except:
            return False
        
        # FTP stress
    def start_monitor(self,domonitorlist,showlist,chost,cpeiplist,ftpiplist,imsilist):
        # check status thread
        checkthreadlist = []
        # cpeping
        if "UEPING_D" in domonitorlist:
            cpepingthread = threading.Thread(target=self._pinglist_check,
                                      name = "cpeipcheck",
                                      args=(cpeiplist,"ping","Database/cpeping.db"))
            checkthreadlist.append(cpepingthread)
        # ftpping
        if "FTPPING_D" in domonitorlist:
            ftppingthread = threading.Thread(target=self._pinglist_check,
                                      name = "ftppingchek",
                                      args =(ftpiplist,"ping","Database/ftpping.db"))
            checkthreadlist.append(ftppingthread)
        # cellping
        if "CELLPING_D" in domonitorlist:
            cellpingthread = threading.Thread(target=self._ping_check,
                                       name = "cellpingcheck",
                                       args =(chost,"Database/cellping.db"))
            checkthreadlist.append(cellpingthread)
        # cellrate
        if "CELLRATE_D" in domonitorlist:
            cellratethread = threading.Thread(target=self.syslog_save_rate,
                                      name = "cellratecheck",
                                      args = (chost,"root",
                                              "root123",27149))
            checkthreadlist.append(cellratethread)
        # cellprb
        if "CELLPRB_D" in domonitorlist:
            cellprbthread = threading.Thread(target=self.cell_check_prb,
                                             name="cellprbcheck",
                                             args=(chost,"root",
                                                   "root123",27149))
            checkthreadlist.append(cellprbthread)
        # cell&uestatus
        if "CELLSTATUS_D" in domonitorlist:
            cellinfothread = threading.Thread(target=self.check_uestatus,
                                       name = "cellinfocheck",
                                       args = (showlist,imsilist,chost,
                                               "root","root123", 27149))
            checkthreadlist.append(cellinfothread)
        # cellri
        if "CELLRI_D" in domonitorlist:
            cellrithread = threading.Thread(target=self.cell_check_ri,
                                     name = "cellricheck",
                                     args = (chost,"root",
                                             "root123",27149))
            checkthreadlist.append(cellrithread)
        # cellload
        if "CELLLOAD_D" in domonitorlist:
            cellloadthread = threading.Thread(target=self.cell_check_load,
                                      name = "cellloadcheck",
                                      args = (chost,"root",
                                              "root123",27149))
            checkthreadlist.append(cellloadthread)
       # cellues
        if "CELLUES_D" in domonitorlist:
            celluesthread = threading.Thread(target=self.cell_check_ues,
                                         name = "cellues",
                                         args = (chost,"root",
                                                 "root123",27149))
            checkthreadlist.append(celluesthread)
       # cellrlf
        if "CELLRLF_D" in domonitorlist:
            cellrlfthread = threading.Thread(target=self.cell_check_rlf,
                                            name = "cellrfl",
                                            args = (chost,"root",
                                                    "root123",27149))
            checkthreadlist.append(cellrlfthread)
        for thread in checkthreadlist:
            thread.setDaemon(True)
            thread.start()
        for thread in checkthreadlist:
            thread.join()
        return

class Checkwindow(QWidget):
    def __init__(self,cellip,uelist):
        QWidget.__init__(self)
        self.cellip = cellip
        self.uelist = uelist
        self.items = len(self.uelist)
       
        self.setWindowTitle(u"业务测试监控(Baicells)")
        self.resize(1300,720)
        palette1 = QtGui.QPalette()
        palette1.setColor(self.backgroundRole(), QColor("#90EE90"))
        self.setPalette(palette1)
        self.setAutoFillBackground(True)
      
        self.titlelabel1 = QLabel(u"基站状态")
        self.titlelabel2 = QLabel(u"UE状态")
        self.gridlayout = QtGui.QGridLayout()
        self.gridlayout.setSpacing(0)

        self.gridlayout.addWidget(self.titlelabel1,0,0)
        self.setcell()
        self.setcellstatus()
        self.gridlayout.addWidget(self.titlelabel2,3,0)
        self.setue()
        self.setuestatus()
        self.setLayout(self.gridlayout)
       

    def setue(self):
        self.input5 = QLineEdit(self)
        self.input5.setReadOnly(True)
        self.input5.setText(u'IMSI')
        self.input5.setAlignment(QtCore.Qt.AlignCenter)
        self.gridlayout.addWidget(self.input5, 4, 0)

        self.input50 = QLineEdit(self)
        self.input50.setReadOnly(True)
        self.input50.setText(u'UE附着')
        self.input50.setAlignment(QtCore.Qt.AlignCenter)
        self.gridlayout.addWidget(self.input50, 4, 1)

        self.input6 = QLineEdit(self)
        self.input6.setReadOnly(True)
        self.input6.setText(u'CPE Ping')
        self.input6.setAlignment(QtCore.Qt.AlignCenter)
        self.gridlayout.addWidget(self.input6, 4, 2)

        self.input7 = QLineEdit(self)
        self.input7.setReadOnly(True)
        self.input7.setText(u'FTP Ping')
        self.input7.setAlignment(QtCore.Qt.AlignCenter)
        self.gridlayout.addWidget(self.input7, 4, 3)

        self.input8 = QLineEdit(self)
        self.input8.setReadOnly(True)
        self.input8.setText(u'DL(Mbps)')
        self.input8.setAlignment(QtCore.Qt.AlignCenter)
        self.gridlayout.addWidget(self.input8, 4, 4)

        self.input9 = QLineEdit(self)
        self.input9.setReadOnly(True)
        self.input9.setText(u'UL(Mbps)')
        self.input9.setAlignment(QtCore.Qt.AlignCenter)
        self.gridlayout.addWidget(self.input9, 4, 5)

        self.input10 = QLineEdit(self)
        self.input10.setReadOnly(True)
        self.input10.setText(u'UL_MCS')
        self.input10.setAlignment(QtCore.Qt.AlignCenter)
        self.gridlayout.addWidget(self.input10, 4, 6)

        self.input11 = QLineEdit(self)
        self.input11.setReadOnly(True)
        self.input11.setText(u'DL_MCS')
        self.input11.setAlignment(QtCore.Qt.AlignCenter)
        self.gridlayout.addWidget(self.input11, 4, 7)

        self.input12 = QLineEdit(self)
        self.input12.setReadOnly(True)
        self.input12.setText(u'UL_BLER')
        self.input12.setAlignment(QtCore.Qt.AlignCenter)
        self.gridlayout.addWidget(self.input12, 4, 8)

        self.input13 = QLineEdit(self)
        self.input13.setReadOnly(True)
        self.input13.setText(u'DL_BLER')
        self.input13.setAlignment(QtCore.Qt.AlignCenter)
        self.gridlayout.addWidget(self.input13, 4, 9)

    def setcell(self):
        self.input0 = QLineEdit(self)
        self.input0.setReadOnly(True)
        self.input0.setText(u'CELL')
        self.input0.setAlignment(QtCore.Qt.AlignCenter)
        self.gridlayout.addWidget(self.input0, 1, 0)

        self.input01 = QLineEdit(self)
        self.input01.setReadOnly(True)
        self.input01.setText(u'UE连接数')
        self.input01.setAlignment(QtCore.Qt.AlignCenter)
        self.gridlayout.addWidget(self.input01, 1, 1)

        self.input1 = QLineEdit(self)
        self.input1.setText(u'PING')
        self.input1.setAlignment(QtCore.Qt.AlignCenter)
        self.input1.setReadOnly(True)
        self.gridlayout.addWidget(self.input1, 1, 2)

        self.input2 = QLineEdit(self)
        self.input2.setText(u'UL速率(Mbps)')
        self.input2.setAlignment(QtCore.Qt.AlignCenter)
        self.input2.setReadOnly(True)
        self.gridlayout.addWidget(self.input2, 1, 3)

        self.input3 = QLineEdit(self)
        self.input3.setText(u'DL速率(Mpbs)')
        self.input3.setAlignment(QtCore.Qt.AlignCenter)
        self.input3.setReadOnly(True)
        self.gridlayout.addWidget(self.input3, 1, 4)

        self.input14 = QLineEdit(self)
        self.input14.setText(u'RI_1')
        self.input14.setAlignment(QtCore.Qt.AlignCenter)
        self.input14.setReadOnly(True)
        self.gridlayout.addWidget(self.input14, 1, 5)

        self.input15 = QLineEdit(self)
        self.input15.setText(u'RI_2')
        self.input15.setAlignment(QtCore.Qt.AlignCenter)
        self.input15.setReadOnly(True)
        self.gridlayout.addWidget(self.input15, 1, 6)

        self.input16 = QLineEdit(self)
        self.input16.setText(u'CPU负载')
        self.input16.setAlignment(QtCore.Qt.AlignCenter)
        self.input16.setReadOnly(True)
        self.gridlayout.addWidget(self.input16, 1, 7)

        self.input17 = QLineEdit(self)
        self.input17.setText(u'UL_BLER')
        self.input17.setAlignment(QtCore.Qt.AlignCenter)
        self.input17.setReadOnly(True)
        self.gridlayout.addWidget(self.input17, 1, 8)

        self.input18 = QLineEdit(self)
        self.input18.setText(u'DL_BLER')
        self.input18.setAlignment(QtCore.Qt.AlignCenter)
        self.input18.setReadOnly(True)
        self.gridlayout.addWidget(self.input18, 1, 9)

        self.input19 = QLineEdit(self)
        self.input19.setText(u'UL_PRBU')
        self.input19.setAlignment(QtCore.Qt.AlignCenter)
        self.input19.setReadOnly(True)
        self.gridlayout.addWidget(self.input19, 1, 10)

        self.input20 = QLineEdit(self)
        self.input20.setText(u'DL_PRBU')
        self.input20.setAlignment(QtCore.Qt.AlignCenter)
        self.input20.setReadOnly(True)
        self.gridlayout.addWidget(self.input20, 1, 11)

        self.input21 = QLineEdit(self)
        self.input21.setText(u'RLF_Num')
        self.input21.setAlignment(QtCore.Qt.AlignCenter)
        self.input21.setReadOnly(True)
        self.gridlayout.addWidget(self.input21, 1, 12)

    def setcellstatus(self):
        self.cellshow = QLineEdit(self)
        self.cellshow.setText(self.cellip)
        self.cellshow.setReadOnly(True)
        self.gridlayout.addWidget(self.cellshow, 2, 0)

        self.celluenum = QLineEdit(self)
        self.gridlayout.addWidget(self.celluenum,2,1)
        
        self.cellping = QLineEdit(self)
        self.gridlayout.addWidget(self.cellping,2,2)
        
        self.cellul = QLineEdit(self)
        self.gridlayout.addWidget(self.cellul,2,3)
        
        self.celldl = QLineEdit(self)
        self.gridlayout.addWidget(self.celldl,2,4)

        self.cellri1 = QLineEdit(self)
        self.gridlayout.addWidget(self.cellri1,2,5)

        self.cellri2 = QLineEdit(self)
        self.gridlayout.addWidget(self.cellri2,2,6)

        self.cellcpu = QLineEdit(self)
        self.gridlayout.addWidget(self.cellcpu,2,7)

        self.cellulb = QLineEdit(self)
        self.gridlayout.addWidget(self.cellulb,2,8)

        self.celldlb = QLineEdit(self)
        self.gridlayout.addWidget(self.celldlb,2,9)

        self.cellulp = QLineEdit(self)
        self.gridlayout.addWidget(self.cellulp,2,10)
        
        self.celldlp = QLineEdit(self)
        self.gridlayout.addWidget(self.celldlp,2,11)

        self.cellrlf = QLineEdit(self)
        self.gridlayout.addWidget(self.cellrlf,2,12)


    def setuestatus(self):
        num = 5
        for ue in self.uelist:
            self.ueimsi = QLineEdit(self)
            self.ueimsi.setText(ue)
            self.ueimsi.setReadOnly(True)
            self.gridlayout.addWidget(self.ueimsi, num, 0)
            num += 1
        n = 5
        self.cpestatuslist = []
        self.cpepinglist = []
        self.ftppinglist = []
        self.dlratelist = []
        self.ulratelist = []
        self.ulmcslist = []
        self.dlmcslist = []
        self.ulblerlist = []
        self.dlblerlist = []
        for i in range(self.items):
            self.cpestatus = QLineEdit(self)
            self.cpeping = QLineEdit(self)
            self.ftpping = QLineEdit(self)
            self.dlrate = QLineEdit(self)
            self.ulrate = QLineEdit(self)
            self.ulmcs = QLineEdit(self)
            self.dlmcs = QLineEdit(self)
            self.ulbler = QLineEdit(self)
            self.dlbler = QLineEdit(self)
            self.gridlayout.addWidget(self.cpestatus,n,1)
            self.gridlayout.addWidget(self.cpeping,n,2)
            self.gridlayout.addWidget(self.ftpping,n,3)
            self.gridlayout.addWidget(self.dlrate,n,4)
            self.gridlayout.addWidget(self.ulrate,n,5)
            self.gridlayout.addWidget(self.ulmcs,n,6)
            self.gridlayout.addWidget(self.dlmcs,n,7)
            self.gridlayout.addWidget(self.ulbler,n,8)
            self.gridlayout.addWidget(self.dlbler,n,9)
            self.cpestatuslist.append(self.cpestatus)
            self.cpepinglist.append(self.cpeping)
            self.ftppinglist.append(self.ftpping)
            self.dlratelist.append(self.dlrate)
            self.ulratelist.append(self.ulrate)
            self.ulmcslist.append(self.ulmcs)
            self.dlmcslist.append(self.dlmcs)
            self.ulblerlist.append(self.ulbler)
            self.dlblerlist.append(self.dlbler)
            n += 1

    # cell rate
    def handleDisplay_cellrate(self,data):
        data = data.split(" ")
        self.cellul.setText(data[0])
        self.celldl.setText(data[1])

    # cell prb
    def handleDisplay_cellprb(self, data):
        data = data.split(" ")
        self.cellulp.setText(data[0])
        self.celldlp.setText(data[1])

    # cell bler 
    def handleDisplay_cellbler(self,data):
        data = data.split(" ")
        self.cellulb.setText(data[0])
        self.celldlb.setText(data[1])

    # cell rlf
    def handleDisplay_cellrlf(self,date):
        self.cellrlf.setText(date)

    # cell ping
    def handleDisplay_cellping(self,data):
        self.cellping.setText(data)

    # cell ri
    def handleDisplay_cellri(self,data):
        data = data.split(",")
        self.cellri1.setText(data[0])
        self.cellri2.setText(data[1])

    # cell load
    def handleDisplay_cellcpu(self,data):
        self.cellcpu.setText(data)

    # cell ue count
    def handleDisplay_cellues(self,data):
        self.celluenum.setText(data)

    # ue cpeping
    def handleDisplay_cpeping(self, data):
        data = data.split(" ")
        for i, value in enumerate(self.cpepinglist):
            value.setText(data[i])

    # ue ftpping
    def handleDisplay_ftpping(self,data):
        data = data.split(" ")
        for i, value in enumerate(self.ftppinglist):
            value.setText(data[i])

    # ue rate and status     
    def handleDisplay_uerate(self,data):
        data = data.split(";")
        ueinfo = []
        for dat in data:
            ueinfo.append(dat.split(","))
        for i, value in enumerate(ueinfo):
            self.dlratelist[i].setText(value[0])
            self.ulratelist[i].setText(value[1])

    #ue on/off
    def handleDisplay_ueon(self,data):
        data = data.split(',')
        for i,value in enumerate(self.cpestatuslist):
            value.setText(data[i])

    # ue mcs
    def handleDisplay_uemcs(self,data):
        data = data.split(";")
        ueinfo =[]
        for dat in data:
            ueinfo.append(dat.split(","))
        for i,value in enumerate(ueinfo):
            self.ulmcslist[i].setText(value[0])
            self.dlmcslist[i].setText(value[1])

    # ue bler
    def handleDisplay_uebler(self,data):
        data = data.split(";")
        ueinfo = []
        for dat in data:
            ueinfo.append(dat.split(","))
        for i,value in enumerate(ueinfo):
            self.ulblerlist[i].setText(value[0])
            self.dlblerlist[i].setText(value[1])

# cell bler status         
class Backend_cellbler(QThread):
    update_date = pyqtSignal(QString)
    def run(self):      
        while True:
            try:
                s = shelve.open('cell.db')
                values = s['cell']
                s.close()
                values = ' '.join(values)
            except:
                pass
            self.update_date.emit(QString(values))
            time.sleep(3)

# cell prb status
class Backend_cellprb(QThread):
    update_date = pyqtSignal(QString)
    def run(self):      
        while True:
            try:
                s = shelve.open('Database/cellprb.db')
                values = s['cellprb']
                s.close()
            except:
                pass
            self.update_date.emit(QString(values))
            time.sleep(3)

# cell ues status
class Backend_cellues(QThread):
    update_date = pyqtSignal(QString)
    def run(self):
        while True:
            try:
                s = shelve.open('Database/cellues.db')
                values = s["uecount"]
                s.close()
            except:
                pass
            self.update_date.emit(QString(values))
            time.sleep(3)

class Backend_cellrate(QThread):
    update_date = pyqtSignal(QString)
    def run(self):      
        while True:
            try:
                s = shelve.open('Database/cellrate.db')
                values = s['cellrate']
                s.close()
                values = ' '.join(values)
            except:
                pass
            self.update_date.emit(QString(values))
            time.sleep(3)


class Backend_cellrlf(QThread):
    update_date = pyqtSignal(QString)
    def run(self):
        while True:
            try:
                s = shelve.open('Database/cellrlf.db')
                values = s['rlf']
                s.close()
            except:
                pass
            self.update_date.emit(QString(values))
            time.sleep(3)


class Backend_cellping(QThread):
    update_date = pyqtSignal(QString)
    def run(self):
        while True:
            try:
                s = shelve.open('Database/cellping.db')
                values = s['ping']
                s.close()
            except:
                pass
            self.update_date.emit(QString(values))
            time.sleep(10)    


class Backend_cellri(QThread):
    update_date = pyqtSignal(QString)
    def run(self):
        while True:
            try:
                s = shelve.open('Database/cellri.db')
                values = s['cellri']
                s.close()
            except:
                pass
            self.update_date.emit(QString(values))
            time.sleep(10) 


class Backend_cellcpu(QThread):
    update_date = pyqtSignal(QString)
    def run(self):
        while True:
            try:
                s = shelve.open('Database/load.db')
                values = s['load']
                s.close()
            except:
                pass
            self.update_date.emit(QString(values))
            time.sleep(10)

class Backend_cpeping(QThread):
    update_date = pyqtSignal(QString)
    def run(self):      
        while True:
            try:
                s = shelve.open('Database/cpeping.db')
                values = s['ping']
                s.close()
                values = ' '.join(values)
            except:
                pass
            self.update_date.emit(QString(values))
            time.sleep(10)
                

class Backend_ftpping(QThread):
    update_date = pyqtSignal(QString)
    def run(self):
        while True:
            try:
                s = shelve.open('Database/ftpping.db')
                values = s['ping']
                s.close()
                values = ' '.join(values)
            except:
                pass
            self.update_date.emit(QString(values))
            time.sleep(10)    


class Backend_ueon(QThread):
    update_date = pyqtSignal(QString)
    def run(self):
        while True:
            try:
                s = shelve.open("Database/ueonoff.db")
                values = s["ONOFF"]
                s.close()
            except:
                pass
            self.update_date.emit(QString(values))
            time.sleep(10)
                

class Backend_uerate(QThread):
    update_date = pyqtSignal(QString)
    def run(self):
        while True:
            try:
                s = shelve.open('Database/uerate.db')
                values = s['uerate']
                s.close()
                ueinfo = []
                for val in values:
                    ueinfo.append(','.join(val))
            except:
                pass
            self.update_date.emit(';'.join(ueinfo))
            time.sleep(10)
            
      
class CheckWindow(QtGui.QMainWindow):
    def __init__(self,updatelist,cellip,uelist):
        QtGui.QMainWindow.__init__(self)
        self.updatelist=updatelist
        self.cellip=cellip
        self.uelist=uelist
        w = QtGui.QWidget()
        self.setCentralWidget(w)
        
        self.checkwin = Checkwindow(self.cellip, self.uelist)

        self.setupdate()
        scroll = QtGui.QScrollArea()
        scroll.setWidget(self.checkwin)
        scroll.setAutoFillBackground(True)
        scroll.setWidgetResizable(True)

        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(scroll)
        w.setLayout(vbox)

        self.setWindowTitle(u"业务测试监控(Baicells)")
        self.resize(1300,768)
        self.setWindowFlags(QtCore.Qt.WindowMinimizeButtonHint)

    def setupdate(self):
        doupdatelist = []
        # cellping
        if "CELLPING_V" in self.updatelist:
            cellpings = Backend_cellping(self)
            cellpings.update_date.connect(self.checkwin.handleDisplay_cellping)
            doupdatelist.append(cellpings)
        # cellprb
        if "CELLPRB_V" in self.updatelist:
            cellstatus = Backend_cellprb(self)
            cellstatus.update_date.connect(self.checkwin.handleDisplay_cellprb)
            doupdatelist.append(cellstatus)

        # cellBLER
        # cellrlf
        if "CELLRLF_V" in self.updatelist:
            cellrlfs = Backend_cellrlf(self)
            cellrlfs.update_date.connect(self.checkwin.handleDisplay_cellrlf)
            doupdatelist.append(cellrlfs)
        # celluecount
        if "CELLUES_V" in self.updatelist:
            cellues = Backend_cellues(self)
            cellues.update_date.connect(self.checkwin.handleDisplay_cellues)
            doupdatelist.append(cellues)                      
        # cellrate
        if "CELLRATE_V" in self.updatelist:            
            cellrates = Backend_cellrate(self)
            cellrates.update_date.connect(self.checkwin.handleDisplay_cellrate)
            doupdatelist.append(cellrates)
        # cellri
        if "CELLRI_V" in self.updatelist:
            cellris = Backend_cellri(self)
            cellris.update_date.connect(self.checkwin.handleDisplay_cellri)
            doupdatelist.append(cellris)
        # cellload
        if "CELLLOAD_V" in self.updatelist:
            cellcpus = Backend_cellcpu(self)
            cellcpus.update_date.connect(self.checkwin.handleDisplay_cellcpu)
            doupdatelist.append(cellcpus)
        # uerate
        if "UERATE_V" in self.updatelist:
            uestatuss = Backend_uerate(self)
            uestatuss.update_date.connect(self.checkwin.handleDisplay_uerate)
            doupdatelist.append(uestatuss)
        # cpeping
        if "UEPING_V" in self.updatelist:
            cpepings = Backend_cpeping(self)
            cpepings.update_date.connect(self.checkwin.handleDisplay_cpeping)
            doupdatelist.append(cpepings)
        # ftpping
        if "FTPPING_V" in self.updatelist:
            ftppings = Backend_ftpping(self)
            ftppings.update_date.connect(self.checkwin.handleDisplay_ftpping)
            doupdatelist.append(ftppings)
        # ueon
        if "UEON_V" in self.updatelist:
            ueonupdates = Backend_ueon(self)
            ueonupdates.update_date.connect(self.checkwin.handleDisplay_ueon)
            doupdatelist.append(ueonupdates)
        # uemcs
        # uebler
        for qthread in doupdatelist:
            qthread.start()
"""
test = DoMonitor()
test.start_monitor("192.168.9.149",["192.168.100.103"],["192.168.100.103"],["11111111"])
"""


class DoCheck(QThread):

    def __init__(self,domonitorlist,showlist,chost,cpeiplist,ftpiplist,imsilist):
        QThread.__init__(self)
        self.domonitorlist = domonitorlist
        self.chost = chost
        self.cpeiplist = cpeiplist
        self.ftpiplist = ftpiplist
        self.imsilist = imsilist
        self.showlist = showlist
        
    def run(self):
        checkjob = DoMonitor()
        checkjob.start_monitor(self.domonitorlist,self.showlist,self.chost,
                               self.cpeiplist,self.ftpiplist,self.imsilist) 
            
class SetMonitor(QDialog):
    
    def __init__(self,cpeiplist,ftpiplist,imsilist,ftpargs, ueargs):
        QDialog.__init__(self) 
        self.imsilist = imsilist
        self.checklist = []
        self.showlist = []
        self.cellip = ftpargs['chost']
        self.cpeiplist = cpeiplist
        self.ftpiplist = ftpiplist
        self.ftpargs = ftpargs
        self.ueargs = ueargs
        self.setWindowTitle(u"监控设置")
        palette1 = QtGui.QPalette()
        palette1.setColor(self.backgroundRole(), QColor("#5F9EA0"))
        self.setPalette(palette1)
        self.setAutoFillBackground(True)
        self.createlabel()
        self.createcheckbox()
        self.createbutton()
        self.Layout()

    def createlabel(self):
        self.celllabel = QLabel(u"小区监控设置:")
        self.cell_label0 = QLabel(u"小区Ping测试")
        self.cell_label1 = QLabel(u"UE连接数检查")
        self.cell_label2 = QLabel(u"小区速率监控")
        self.cell_label3 = QLabel(u"小区RI监控")
        self.cell_label4 = QLabel(u"小区负载监控")
        self.cell_label5 = QLabel(u"小区PRB监控")
        self.cell_label6 = QLabel(u"小区BLER监控")
        self.cell_label7 = QLabel(u"RLF检查")
        self.uelabel = QLabel(u"UE监控设置:")
        self.ue_label0 = QLabel(u"UE附着状态监控")
        self.ue_label1 = QLabel(u"UE Ping测试")
        self.ue_label2 = QLabel(u"UE(FTP)Ping测试")
        self.ue_label3 = QLabel(u"UE速率监控")
        self.ue_label4 = QLabel(u"UEMCS监控")
        self.ue_label5 = QLabel(u"UEBLER监控")     

    def createcheckbox(self):
        self.checkboxs = []
        self.checkbox1 = QtGui.QCheckBox()
        self.checkbox1._id = "CELLPING_D"
        self.checkbox1._value = "CELLPING_V"
        self.checkbox1.stateChanged.connect(self.checks)
        self.checkboxs.append(self.checkbox1)
        
        self.checkbox2 = QtGui.QCheckBox()
        self.checkbox2._id = "CELLUES_D"
        self.checkbox2._value = "CELLUES_V"
        self.checkbox2.stateChanged.connect(self.checks)
        self.checkboxs.append(self.checkbox2)

        self.checkbox3 = QtGui.QCheckBox()
        self.checkbox3._id = "CELLRATE_D"
        self.checkbox3._value = "CELLRATE_V"
        self.checkbox3.stateChanged.connect(self.checks)
        self.checkboxs.append(self.checkbox3)

        self.checkbox4 = QtGui.QCheckBox()
        self.checkbox4._id = "CELLRI_D"
        self.checkbox4._value = "CELLRI_V"
        self.checkbox4.stateChanged.connect(self.checks)
        self.checkboxs.append(self.checkbox4)

        self.checkbox5 = QtGui.QCheckBox()
        self.checkbox5._id = "CELLLOAD_D"
        self.checkbox5._value = "CELLLOAD_V"
        self.checkbox5.stateChanged.connect(self.checks)
        self.checkboxs.append(self.checkbox5)

        self.checkbox6 = QtGui.QCheckBox()
        self.checkbox6._id = "CELLPRB_D"
        self.checkbox6._value = "CELLPRB_V"
        self.checkbox6.stateChanged.connect(self.checks)
        self.checkboxs.append(self.checkbox6)

        self.checkbox7 = QtGui.QCheckBox()
        self.checkbox7._id = "CELLSTATUS_D"
        self.checkbox7._value = "CELLBLER_V"
        self.checkbox7.stateChanged.connect(self.checks)
        self.checkboxs.append(self.checkbox7)

        self.checkbox8 = QtGui.QCheckBox()
        self.checkbox8._id = "CELLRLF_D"
        self.checkbox8._value = "CELLRLF_V"
        self.checkbox8.stateChanged.connect(self.checks)
        self.checkboxs.append(self.checkbox8)

        self.checkbox9 = QtGui.QCheckBox()
        self.checkbox9._id = "CELLSTATUS_D"
        self.checkbox9._value = "UEON_V"
        self.checkbox9.stateChanged.connect(self.checks)
        self.checkboxs.append(self.checkbox9)

        self.checkbox10 = QtGui.QCheckBox()
        self.checkbox10._id = "UEPING_D"
        self.checkbox10._value = "UEPING_V"
        self.checkbox10.stateChanged.connect(self.checks)
        self.checkboxs.append(self.checkbox10)

        self.checkbox11 = QtGui.QCheckBox()
        self.checkbox11._id = "FTPPING_D"
        self.checkbox11._value = "FTPPING_V"
        self.checkbox11.stateChanged.connect(self.checks)
        self.checkboxs.append(self.checkbox11)

        self.checkbox12 = QtGui.QCheckBox()
        self.checkbox12._id = "CELLSTATUS_D"
        self.checkbox12._value = "UERATE_V"
        self.checkbox12.stateChanged.connect(self.checks)
        self.checkboxs.append(self.checkbox12)

        self.checkbox13 = QtGui.QCheckBox()
        self.checkbox13._id = "CELLSTATUS_D"
        self.checkbox13._value = "UEMCS_V"
        self.checkbox13.stateChanged.connect(self.checks)
        self.checkboxs.append(self.checkbox13)

        self.checkbox14 = QtGui.QCheckBox()
        self.checkbox14._id = "CELLSTATUS_D"
        self.checkbox14._value = "UEBLER_V"
        self.checkbox14.stateChanged.connect(self.checks)
        self.checkboxs.append(self.checkbox14)

    def checks(self,start):
        checkbox=self.sender()#获取发射信号对象
        if start==Qt.Checked:
            self.checklist.append(checkbox._id)
            self.showlist.append(checkbox._value)
        elif start==Qt.Unchecked:
            try:
                self.checklist.remove(checkbox._id)
                self.showlist.remove(checkbox._value)
            except:
                pass

    def createbutton(self):
        self.startbutton = QtGui.QPushButton(u"启动监控")
        self.connect(self.startbutton, QtCore.SIGNAL('clicked()'),
                     self.Onstart)
        self.setbutton = QtGui.QPushButton(u"查看监控")
        self.connect(self.setbutton, QtCore.SIGNAL('clicked()'),
                     self.Oncheck)
        self.setallbutton = QtGui.QPushButton(u"全选")
        self.connect(self.setallbutton, QtCore.SIGNAL('clicked()'),
                     self.Onsetall)
    
    def Layout(self):
        baseLayout = QGridLayout()
        acer1 = QtGui.QSpacerItem(10,24)
        acer2 = QtGui.QSpacerItem(700,10)
        # title
        baseLayout.addWidget(self.celllabel, 0,0)
        baseLayout.addWidget(self.uelabel, 17,0)

        # cell label
        baseLayout.addWidget(self.cell_label0,1,0)
        baseLayout.addItem(acer1,2,0)
        baseLayout.addWidget(self.cell_label1,3,0)
        baseLayout.addItem(acer1,4,0)
        baseLayout.addWidget(self.cell_label2,5,0)
        baseLayout.addItem(acer1,6,0)
        baseLayout.addWidget(self.cell_label3,7,0)
        baseLayout.addItem(acer1,8,0)
        baseLayout.addWidget(self.cell_label4,9,0)
        baseLayout.addItem(acer1,10,0)
        baseLayout.addWidget(self.cell_label5,11,0)
        baseLayout.addItem(acer1,12,0)
        baseLayout.addWidget(self.cell_label6,13,0)
        baseLayout.addItem(acer1,14,0)
        baseLayout.addWidget(self.cell_label7,15,0)
        n = 1
        for i in range(8):
            baseLayout.addWidget(self.checkboxs[i],i+n,1)
            n+=1 
        baseLayout.addItem(acer1,16,0)
        # ue Label
        baseLayout.addWidget(self.ue_label0,18,0)
        baseLayout.addItem(acer1,19,0)
        baseLayout.addWidget(self.ue_label1,20,0)
        baseLayout.addItem(acer1,21,0)
        baseLayout.addWidget(self.ue_label2,22,0)
        baseLayout.addItem(acer1,23,0)
        baseLayout.addWidget(self.ue_label3,24,0)
        baseLayout.addItem(acer1,25,0)
        baseLayout.addWidget(self.ue_label4,26,0)
        baseLayout.addItem(acer1,27,0)
        baseLayout.addWidget(self.ue_label5,28,0)
        n=18
        for i in range(6):
            baseLayout.addWidget(self.checkboxs[i+8],i+n,1)
            n+=1
        footer2Layout = QHBoxLayout()
        baseLayout.addItem(acer1, 29,0)
        baseLayout.addItem(acer2, 29,1)
        footer2Layout.addWidget(self.setallbutton)
        footer2Layout.addWidget(self.startbutton)
        footer2Layout.addWidget(self.setbutton)

        baseLayout.setSizeConstraint(QLayout.SetFixedSize)
        baseLayout.setSpacing(10)
        baseLayout.addLayout(footer2Layout,29,3)
        self.setLayout(baseLayout)

    def Oncheck(self):
        self.checkwin = CheckWindow(self.showlist,self.cellip,self.imsilist)
        self.checkwin.show()

    def Onstart(self):
        self.checkthread = DoCheck(self.checklist,self.showlist,self.cellip,
                              self.cpeiplist,self.ftpiplist,self.imsilist)
        self.checkthread.start()

    def Onsetall(self):
        for check in self.checkboxs:
            check.setChecked(True)


