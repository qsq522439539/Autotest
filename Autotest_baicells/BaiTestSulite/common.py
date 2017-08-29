#!/usr/bin/env python
#coding=utf-8
import paramiko
import os
import subprocess
import string
import time
import datetime
import sys
import math
import re
import string
import linecache
import multiprocessing
import threading
import Queue
import xml.dom.minidom
import logging
import struct
import socket


from ftplib import FTP
from xml.dom import  minidom

reload(sys) 
sys.setdefaultencoding('utf-8')

class TestPerformance:
    def __init__(self):
       self.logger = logging.getLogger('test')

    ## common
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

    def _startmultthread(self,threads,DAEMON,JOIN):
        if DAEMON:
            for thread in threads:
                thread.setDaemon(True)
        for thread in threads:
            thread.start()
        if JOIN:
            for thread in threads:
                thread.join()
        return

   # cell rate check
    def dogetrate(self,hostname, username, password, port):
        cmd = "grep dlTtlTpt /tmp/log/syslog | awk -F ' ' '{print $7,$9}' | tr -d 'ulTtlTpt=dlTtlTpt=' | tail -n 1 | tr -d '\n'"
        try:
            client=paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(hostname, port, username, password)  
            stdin,stdout,stderr=client.exec_command(cmd)
            rate=stdout.read()
            client.close()
            if rate is not None:
                rate = rate.split(' ')
                if len(rate) > 0:
                    return rate
        except:
            return ["0.00","0.00"]
            
    # Save syslog rate 
    def syslog_save_rate(self,checkmode,hostname,expectspeed,testtime,
                         logfile,username,password, port):
        port = int(port)
        time.sleep(10)
        testtime = int(testtime)
        logfile=logfile + "%s.csv" % hostname
        f = open(logfile, 'a')
        f.write('Time, UL_Rate, DL_Rate\n')
        starttime = time.time()
        while time.time() - starttime < testtime-10:
            status = self.dogetrate(hostname,username, password, port)
            f = open(logfile, 'a')
            f.write('%s, %s, %s\n' % (time.strftime('%Y:%m:%d:%H:%M:%S'),status[0], status[1]))
            f.close()
            if checkmode == "DOWN":
                rate = status[1]
                print rate
                rate = float(rate) * 1024 * 1024
                if rate < expectspeed:
                    self.Status.put("FAIL")
            else:
                rate = status[0]
                print rate
                rate = float(rate) * 1024 * 1024
                if rate < expectspeed:
                    self.Status.put("FAIL")      
            time.sleep(15)

    # FTP TEST
    ## download fun
    def _Download_FTP(self,testtime=60, remotepath="lp02",localpath="F:/TMP/lp01",
                      host="192.168.9.79", username="ftpuser", password="888888"):
        ''' 
        host: the conneced host IP address  
        username: login host name   
        password: login host password   
        remotepath: storage path of download file   
        localpath： local path of saved file
        '''
        testtime=int(testtime)
        ftp = FTP()
        try:
            ftp.set_debuglevel(2)
            ftp.connect(host, 21)
            ftp.login(username, password)
        except:
            print("FTP login faild %s" %host)
            return False
        try:
            ftp.set_pasv(True)
            ftp.dir()
        except:
            ftp.set_pasv(False)
        bufsize = 1024
        starttime = time.time()
        print starttime
        teststatus = []
        while True:
            timenow = time.time()
            if timenow - starttime > testtime:
                break  
            fp = open(localpath, 'w')
            try:  
                ftp.retrbinary('RETR ' + remotepath, fp.write, bufsize)
            except:
                break
        fp.close()
        ftp.set_debuglevel(0)
        ftp.quit()
        return True

    def _Upload_FTP(self, testtime=60, remotepath="lp02",localpath="F:/TMP/lp01",
                    host="192.168.9.79", username="ftpuser", password="888888"):
        '''
        FTP upload service.
        host: the conneced host IP address
        username: login host name
        password: login host password
        remotepath: storage path of download file
        localpath： local path of saved file
        '''
        ftp = FTP()
        try:
            ftp.set_debuglevel(2)
            ftp.connect(host, 21)
            ftp.login(username, password)
        except:
            print("FTP login faild %s" %host)
            return False
        try:
            ftp.set_pasv(True)
            ftp.cwd('/home/ftpuser/') 
        except:
            ftp.set_pasv(False)
            ftp.cwd('/home/ftpuser/') 
        bufsize = 1024
        starttime = time.time()
        teststatus = []
        while True:
            timenow = time.time()
            if timenow - starttime > testtime:
                break
            fp = open(localpath, 'r')
            try:
                ftp.storbinary('STOR ' + remotepath, fp, bufsize)
            except:
                break 
        ftp.set_debuglevel(0)
        fp.close()
        ftp.quit()
        return True

    def Ftp_Perftest(self,testmode="UP",expectspeed="70M",testtime=600,
                     cellip='192.168.107.237',downloadfile="lp01",localpath="F:/TMP/lp01",
                     uppath="F:/TMP/",upfile="lpup0",ftpserver="192.168.9.79",
                     ftpuser="ftpuser", logfile="F:/TMP/",ftppd="888888",
                     sshpw="baicells",port=22,sshname="root"):
        expectspeed = self._getnumbits(expectspeed)
        remotepath="/home/ftpuser/" + downloadfile
        testtime = int(testtime)
        self.Status = Queue.Queue()
        threads =[]
        if testmode == "DOWN":
            for i in range(10):
                ftptest = threading.Thread(target=self._Download_FTP,
                                           name="downloadftp%s"%i,
                                           args=(testtime,remotepath,localpath,
                                                 ftpserver,ftpuser,ftppd))
                threads.append(ftptest)
            ftprate = threading.Thread(target=self.syslog_save_rate,
                                       name="getrate",
                                       args=(testmode,cellip,expectspeed,
                                             testtime,logfile,'root','root123',27149))
        else:
            for i in range(10):
                filename = upfile + "%s" %i
                uppath1 = uppath +filename
                ftptest = threading.Thread(target=self._Upload_FTP,
                                           name = "uploadftp%s"%i,
                                           args=(testtime,filename,uppath1,
                                                 ftpserver,ftpuser,ftppd))
                threads.append(ftptest)
            ftprate = threading.Thread(target=self.syslog_save_rate,
                                       name="getrate",
                                       args=(testmode,cellip,expectspeed,
                                             testtime,logfile,'root','root123',27149))
        ftprate.setDaemon(True)
        ftprate.start()
        self._startmultthread(threads,True,True)
        while not self.Status.empty():
            if self.Status.get() == "FAIL":
                return False
        return True


    def _ping_test(self, testtime, targetaddress, size, tmplog):
        testtime=int(testtime)
        testcmd = "ping %s -l %s -t" % (targetaddress,size)
        #调用系统命令
        p = subprocess.Popen(testcmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        starttime = time.time()
        while time.time() - starttime < testtime:
            f = open(tmplog, 'a')
            log = p.stdout.readline()
            print log
            f.write(log)
            f.close()
        p.kill()
        return True


    def ping_checkstatus(self,tmplog="F:/TMP/ping.txt"):
        num_lines = sum(1 for line in open(tmplog,"rb"))
        count=0
        REPATH = re.compile(r'TTL')
        for line in open(tmplog, 'rb'):
            if REPATH.findall(line):
                count+=1
        if num_lines - count < 3:
            return True
        else:
            return False
            
            
    def ping_background(self,testtime=60, targetaddress="192.168.9.79",size=2048,tmplog="F:/TMP/ping.txt"):
        if os.path.exists(tmplog):
            os.remove(tmplog)
        p = multiprocessing.Process(args=(testtime,targetaddress,size,tmplog,),target=self._ping_test)
        p.start()
        time.sleep(1)
        if os.path.exists(tmplog):
            print "ping test start ok"
            return True
        else:
            print "ping test start fail"
            return False

    def _checkcpestatus(self,cpe,password):
        try:
            client=paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(cpe,22,"root", password)
            return True
        except:
            return False

    def _dosshcmd(self,host,port,cmd,password,Rtype=False):
        try:
            client=paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(host,port,"root", password)
            stdin,stdout,stderr=client.exec_command(cmd)
            status = stdout.read()
            if Rtype:
                if status == "" or status == None:
                    return True
                else:
                    return False
            else:
                return status
        except:
            if Rtype:
                return False
            else:
                return

    def checkuenum(self,host):
        uecmd = "mibcli get  FAP.0.UE_COUNT | awk -F= '{print $2}' | tr -d '\n '"
        uenum = self._dosshcmd(host,27149,uecmd,"root123",False)
        return uenum 

    def _docpereboot(self,host,password):
        for i in range(3):
            status = self._dosshcmd(host,22,"reboot",password,True)
            if status:
                return
        self.dostatus.put(host)

    def _startmultthread(self,threads,DAEMON,JOIN):
        if DAEMON:
            for thread in threads:
                thread.setDaemon(True)
        for thread in threads:
            thread.start()
        if JOIN:
            for thread in threads:
                thread.join()
        return

    def uepingtest(self,iplist):
        RESULT = True
        Faillist = []
        for i in range(5):
            for ip in iplist:
                testcmd = "ping %s -n 3 -l 1500" % ip
                p = subprocess.Popen(testcmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                p.wait()
                log = p.stdout.read()
                if "TTL" in log:
                    self.logger.info("%s is ping pass" % ip)
                else:
                    Faillist.append(ip)
            if len(Faillist) > 0:
                time.sleep(3)
            else:
                return True
        return False

    def rebootcpe(self,host,cpelist,password="Si8a&2vV9"):
        docpelist = []
        self.dostatus = Queue.Queue()
        for i,cpe in enumerate(cpelist):
            docpereboot = threading.Thread(target=self._docpereboot,
                                       name="job%s"%i,
                                       args=(cpe,password))
            docpelist.append(docpereboot)
        self._startmultthread(docpelist,True,True)
        RESULT=True
        while not self.dostatus.empty():
            result = self.dostatus.get()
            if result is not "":
                RESULT=False
                self.logger.error("%s is reboot faild" % self.dostatus.get())
        if not RESULT:
            return False
        for i in range(10):
            time.sleep(30)
            uenum = self.checkuenum(host)
            self.logger.info("%s ues is connected now" % uenum)
            if int(uenum) == len(cpelist):
                return True
        self.logger.error("Some ue is not attaced in 300s")
        return False

    def add_mme_egw(self,host,mmeerrorip,mmeips,tunnel):
        cmd1 = "ipsec status tunnel%s | grep '===' | awk -F' ' '{print $2}' | awk -F/ '{print $1}' | tr -d '\n'"%str(tunnel+1)
        ipsecip = self._dosshcmd(host,27149,cmd1,"root123",False)
        cmd3="route add -host %s gw %s " % (ipsecip,mmeerrorip[tunnel][0])
        add1 = self._dosshcmd(mmeips[tunnel][0],22,cmd3,"baicells",True)
        if add1:
            self.logger.info("%s add error gw sucessful" % ipsecip)
        else:
            self.logger.error("%s add error gw faild" % ipsecip)

    def delete_mme_gw(self,host,mmeips,tunnel):
        cmd1 = "ipsec status tunnel%s | grep '===' | awk -F' ' '{print $2}' | awk -F/ '{print $1}' | tr -d '\n'"%str(tunnel+1)
        ipsecip = self._dosshcmd(host,27149,cmd1,"root123",False)
        cmd3 = "route del -host %s" % ipsecip
        del1 = self._dosshcmd(mmeips[tunnel][0],22,cmd3,"baicells",True)
        if del1:
            self.logger.info("%s del error gw sucessfull" % ipsecip)
        else:
            self.logger.error("%s del error gw faild" % ipsecip)
      

    def win_do_cmd(self,cmd):
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        p.wait()
        return

    def check_ip_in_ipsegment(self,targetip,ip,mask):
        '''Returns the IP of the specified network segment.
        Default mask is "255.255.255.0".
        '''
        ip=str(ip)
        targetip=str(targetip)
        ip_addr = struct.unpack('>I',socket.inet_aton(ip))[0]
        mask_addr = struct.unpack('>I',socket.inet_aton(mask))[0]
        ip_min = ip_addr & (mask_addr & 0xffffffff)
        ip_max = ip_addr | (~mask_addr & 0xffffffff)
        ip_target = struct.unpack('>I',socket.inet_aton(targetip))[0]
        if ip_target in range(ip_min,ip_max):
            return True
        else:
            return False

    def check_ip_mac_insyslog(self,host,ip,mac):
        cmd = "grep %s /tmp/log/syslog | grep -q %s ;echo $? | tr -d '\n'" % (ip,mac)
        result = self._dosshcmd(host,27149,cmd,"root123")
        if result == "0":
            return True
        else:
            return False

    def _thread_ping_backround(self,iplist,tmplog):
        while True:
            while not self.Signal.empty():
                if self.Signal.get() == "STOP":
                    return
            NUM=0
            for ip in iplist:
                testcmd = "ping %s -n 3" % ip
                p = subprocess.Popen(testcmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                p.wait()
                log = p.stdout.read()
                if "TTL" in log:
                    NUM+=1
            self.logger.info("There is %s cpe ping pass" % NUM)
            f = open(tmplog, 'a')
            f.write("UEPINGPASSNUM:%s\n"%NUM)
            f.close()
            time.sleep(3)
        return 
           
    def cpe_ping_background(self,iplist,tmplog="cpeping.txt"):
        if os.path.exists(tmplog):
            os.remove(tmplog)
        self.Signal = Queue.Queue()
        self.logger.info("start ftp ping")
        p = threading.Thread(target=self._thread_ping_backround,args=(iplist,tmplog,))
        p.start()
        time.sleep(5)
        if os.path.exists(tmplog):
            self.logger.info("cpe backround ping test start ok")
            return True
        else:
            self.logger.error("cpe backround ping test start fail")
            return False

    def cpe_ping_pass_num(self,tmplog="cpeping.txt"):
        REPATH = re.compile(r'UEPINGPASSNUM:(.*?)$')
        pingpasslist = []
        for line in open(tmplog, 'rb'):
            num = REPATH.findall(line)
            if num is not None:
                pingpasslist.append(num[0])
        return pingpasslist[-1]

    def check_ue_connect_mme(self,imsilist,mmeip):
        imsimme = {}
        cmd = "mysql -e 'use OAM; select imsi from current_mme_ue;'"
        mmelist1=[]
        mmelist2=[]
        imsilog = self._dosshcmd(mmeip[0],22,cmd,'baicells',False)
        for imsi in imsilist:
            if imsi in imsilog:
                mmelist1.append(imsi)
            else:
                mmelist2.append(imsi)
        imsimme[mmeip[0]] = mmelist1
        imsimme[mmeip[1]] = mmelist2
        return imsimme

    def set_cell_eth_down(self,cellip):
        try:
            client=paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(cellip,27149,"root", "root123")
            stdin,stdout,stderr=client.exec_command("ifconfig eth2 down")
            client.close()
            return True
        except:
            return False

    def check_epc_sctp(self,host,mmeiplist):
        cmd1 = "ipsec status tunnel%s | grep '===' | awk -F' ' '{print $2}' | awk -F/ '{print $1}' | tr -d '\n'"%str(tunnel+1)
        ipsecip = self._dosshcmd(host,27149,cmd1,"root123",False)
        client=paramiko.SSHClient()
        cmd_netdev = "ifconfig | sed -n -e '/^[^\s]*:\s*flags/{N;/%s/p}' | tr -d '\n' | awk -F: '{print $1}' | tr -d '\n'" %mmeiplist[tunnel]
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(mmeip, 22, "root", "baicells")
        stdin,stdout,stderr=client.exec_command(cmd_netdev)
        netdev = stdout.read()
        cmd_tshark = "tshark -i %s host %s -Y sctp" % (netdev, ipsecip)
        ssh = client.invoke_shell()
        time.sleep(1)
        ssh.send(cmd_tshark)
        ssh.send('\n')
        starttime = time.time()
        while time.time() - starttime < 100:
            resp = ssh.recv(1024)
            if "SCTP" in resp:
                client.close()
        client.close()
        return False

    # iperf test
    def _server_iperf_exit(self, iperfpid, hostname="192.168.9.79",
                           username="root", password="baicells",port="22"):
        """
        funcition: kill server's process
        """
        port = int(port)
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, port, username, password)
        stdin,stdout,stderr=client.exec_command("kill -9 %s ;echo $? | tr -d '\n'" % iperfpid)
        returncode = stdout.read()
        print returncode
        if int(returncode) > 0:
            print "iperf process  %s exit faild " % iperfpid
            return False
        else:
            print "iperf process %s exit successful" % iperfpid
            return True

    def _client_iperf_exit(self, pid):
        """
        function: kill client's process
        """
        try:
            os.system("taskkill /F /T /PID %s" % pid)
            print "%s pid exit sucessful" % pid
            return True
        except:
            print "%s pid exit have some error" % pid
            return False

    def _cilent_thread_exit(self, thread):
        """
        function: kill client's process
        """
        try:
            pid = thread.pid()
            thread.kill()
            print "thread %s exit faild" % pid
            return True
        except:
            print "thread %s exit faild" % pid
            return False

    # windows iperf recive
    def _iperf_windows_recive(self, listingmode,testtime,
                              iperfpath,
                              listingport,interval):
        if listingmode == "UDP":
            cmd = "%s -s -u -i %s -p %s" %(iperfpath, interval,listingport)
        else:
            cmd = "%s -s -i %s -p %s" % (iperfpath, interval,listingport)
        p = subprocess.Popen(cmd,stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        checktime = int(testtime)/int(interval)
        starttime = time.time()
        for i in range(7):
            print p.stdout.readline()
            time.sleep(1)
        for i in range(checktime):
            line = p.stdout.readline()
            print line
            time.sleep(interval)
            # loss check  
            lossrate = re.findall(r'\((.*?)%\)',line,re.S)
            timelog = re.findall(r'\] (.*?)\ sec',line,re.S)
            if len(lossrate) > 0:
                if float(lossrate[0]) > 0:
                    self.Status.put("LOSS")
            # testtime check
            if len(timelog) > 0:
                timelist= timelog[0].split('-')
                if testtime in timelist:
                    print "test finsh"
                    p.kill()
                    return True
            else:
                p.kill()
                self.Status.put("BREAK")
                return False
        p.kill()
        return

    # windows iperf send
    def _iperf_windows_send(self,checkmode,listingmode,size,testtime,
                            iperfpath,serverip,interval, listingport):
        if listingmode == "UDP":
            testcmd = "%s -u -c %s -b %s -l 1024 -t %s -i %s -p %s" %(iperfpath,serverip,size,
                                                                      testtime,interval,listingport)
        else:
            testcmd = "%s -c %s -b %s -l 1024 -t %s -i %s -p %s" %(iperfpath,serverip,size,
                                                                   testtime,interval,listingport)
        starttime = time.time()
        p = subprocess.Popen(testcmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        returncode = p.poll()
        if checkmode == "PER":
            stdout, stderr = p.communicate()
            print stdout
        else:            
            if listingmode == "TCP":
                for i in range(5):
                    print p.stdout.readline()
                    time.sleep(1)
                ncount = int(testtime) / int(interval)
                n = 0
                while returncode is None:
                    line = p.stdout.readline()
                    n += 1
                    returncode = p.poll()
                    print line
                    line = line.strip()
                    test = re.findall(r'Bytes  (.*?)bits/sec',line,re.S)
                    if len(test) > 0:
                        test = "".join(test[0].split())
                        print test
                if n < ncount :
                    print "test is break"
                    self.Status.put("BREAK")
            else:
                stdout, stderr = p.communicate()
                print stdout
        return

    # linux iperf recive
    def _iperf_linux_recive(self,listingmode="UDP", interval=10,listingport="27141",
                            hostname="192.168.9.79", username="root", password="baicells",
                            port="22"):
        '''
        server:linux
        function: performance test
        type:iperf recive
        '''
        port = int(port)
        client=paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, port, username, password)
        if listingmode == "UDP":
            cmd_start_server = "echo "" > iperf.log;iperf -s -u -i %s -p %s > iperf.log &" % (interval,listingport)
        else:
            cmd_start_server = "iperf -s -i %s -p %s & " % (interval,listingport)
        stdin,stdout,stderr=client.exec_command(cmd_start_server)
        time.sleep(1)
        stdin,stdout,stderr = client.exec_command("ps aux | grep iperf | grep %s | head -n 1 | awk -F ' ' '{printf $2}' | tr -d '\n'" % listingport)
        iperfpid = stdout.read()
        client.close()
        if iperfpid:
            print "iperf server start by pid %s" % iperfpid
            return iperfpid
        else:
            return None

    # linux iperf send
    def _iperf_linux_send(self,size="120m",testtime=60, listingmode="UDP",
                          clientip="192.168.100.103",interval=10,
                          serverip="192.168.9.79",
                          listingport="27141", username="root", password="baicells", port=22):
        port = int(port)
        client=paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(serverip, port, username, password)
        if listingmode == "UDP":
            cmd_send = "echo "" > iperf.log;iperf -u -c %s -b %s -l 1024 -t %s -i %s -p %s > iperf.log &" %(clientip,
                                                                            size, testtime,
                                                                            interval,listingport)
        else:
            cmd_send = "echo "" > iperf.log;iperf -c %s -b %s -l 1024 -t %s -i %s -p %s > iperf.log &" %(clientip, size,
                                                                       testtime, interval,
                                                                       listingport)
        stdin,stdout,stderr=client.exec_command(cmd_send)
        client.close()
        return True


    # iperf upload speed test

    def _iperf_speed_upload(self,testmode,hostname,size,testtime,exportrate,
                            iperfpath,interval,serverip,logfile,
                            listingport, username,password, port):
        # linux iperf recive start
        self.Status = Queue.Queue()
        exportrate = self._getnumbits(exportrate)
        serverpid = self._iperf_linux_recive(testmode,interval,listingport,
                                        serverip,username, password,port)
        # windows iperf send start
        client_send = threading.Thread(target=self._iperf_windows_send,name="client",
                                       args=("PER",testmode,size,testtime,iperfpath,serverip,interval,listingport))
        client_send.setDaemon(True)
        client_send.start()
        # cell rate check
        cell_check = threading.Thread(target=self.syslog_save_rate,name="check",
                                      args=("UL",hostname,exportrate,testtime,
                                            logfile,username,"root123", 27149))
        cell_check.setDaemon(True)
        cell_check.start()
        cell_check.join()
        self._server_iperf_exit(serverpid,serverip,
                                username, password,port)
        while not self.Status.empty():
            if self.Status.get() == "FAIL":
                return False
            if self.Status.get() == "BREAK":
                return False
        return True

    def _iperf_speed_download(self,testmode,hostname,size, testtime, exportrate,
                              iperfpath,interval,clientip,serverip,logfile,
                              listingport, username,password, port):
        # windows iperf recive start
        self.Status = Queue.Queue()
        exportrate = self._getnumbits(exportrate)
        server_recive = threading.Thread(target = self._iperf_windows_recive,
                                         name = "recive",
                                         args=(testmode,testtime,
                                               iperfpath,listingport,interval))
        server_recive.setDaemon(True)
        server_recive.start()
        # linux iperf send start
        self._iperf_linux_send(size,testtime, testmode,clientip,interval,
                               serverip,listingport, username, password,port)
        #cell rate check
        cell_check = threading.Thread(target=self.syslog_save_rate,name="check",
                                      args=("UL",hostname,exportrate,testtime,
                                            logfile,username,"root123", 27149))
        cell_check.setDaemon(True)
        cell_check.start()
        cell_check.join()
        server_recive.join()
        while not self.Status.empty():
            if self.Status.get() == "FAIL":
                return False
            if self.Status.get() == "BREAK":
                return False
        return True
        
                                            
    # iperf speed test
    def iperf_speed_test(self,mode="DOWN",testmode="UDP",testtime=60,clientip="109.10.10.8",size="120m",
                         hostname="192.168.9.149",exportate="3M",
                         iperfpath="E:\iperf2\iperf.exe", interval=10,
                         serverip="192.168.9.79",logfile="F:/TMP/",
                         listingport="27141", username="root",
                         password="baicells", port=22):
        """
        support:udp/tcp
        iperf recive: linux server
        iperf send: window control pc
        """
        if mode == "UP":
            result = self._iperf_speed_upload(testmode,hostname,size,testtime,exportate,
                                              iperfpath, interval,serverip,logfile,
                                              listingport,username,password, port)
        else:
            result = self._iperf_speed_download(testmode,hostname,size, testtime,exportate,
                                                iperfpath,interval,clientip,serverip,logfile,
                                                listingport, username,password,port)
        if result:
            print "tets ok"
        else:
            print "test fail"
        return result

    # linux udp loss check
    def _iperf_linux_losscheck(self,serverip,testtime,interval,username,password,port):
        starttime = time.time()
        while time.time() - starttime < testtime:
            try:
                client=paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(serverip, port, username, password)
                stdin,stdout,stderr=client.exec_command("cat iperf.log | grep MBytes | awk -F'(' '{print $2}' | awk -F'%' '{print $1}' | tail -n 1 | tr -d '\n'")
                client.close()
                returncode = stdout.read()
                if returncode is not "":
                    if returncode > 0:
                        print "There is some loss"
                        self.Status.put("LOSS")
                time.sleep(interval)
            except:
                pass
        return 
 
    # iperf stress upload test
    def _iperf_stress_upload(self,testmode,size,testtime,
                            iperfpath,interval,serverip,
                            listingport, username,password, port):
        # linux iperf recive start
        self.Status = Queue.Queue()
        serverpid = self._iperf_linux_recive(testmode,interval,listingport,
                                        serverip,username, password,port)
        # windows iperf send start
        client_send = threading.Thread(target=self._iperf_windows_send,name="client",
                                       args=("STB",testmode,size,testtime,iperfpath,serverip,interval,listingport))
        client_send.setDaemon(True)
        client_send.start()
        if testmode == "UDP":
            loss_check = threading.Thread(target=self._iperf_linux_losscheck,name="check",
                                          args=(serverip,testtime,interval,username,password,22))
            loss_check.setDaemon(True)
            loss_check.start()
        client_send.join()
        self._server_iperf_exit(serverpid,serverip,
                                username, password,port)
        while not self.Status.empty():
            if self.Status.get() == "BREAK":
                return False
            if self.Status.get() == "LOSS":
                return False
        return True

    # iperf stress download test
    def _iperf_stress_download(self,testmode,size, testtime,
                               iperfpath,interval,clientip,serverip,
                               listingport, username,password, port):
        # windows iperf recive start
        self.Status = Queue.Queue()
        server_recive = threading.Thread(target = self._iperf_windows_recive,
                                         name = "recive",
                                         args=(testmode,testtime,
                                               iperfpath,listingport,interval))
        server_recive.setDaemon(True)
        server_recive.start()
        # linux iperf send start
        self._iperf_linux_send(size,testtime, testmode,clientip,interval,
                               serverip,listingport, username, password,port)
        #cell rate check
        server_recive.join()
        while not self.Status.empty():
            if self.Status.get() == "LOSS":
                return False
            if self.Status.get() == "BREAK":
                return False
        return True
        
    # iperf stress test
    def iperf_stress_test(self,mode="UP",testmode="TCP",testtime=60,clientip="109.10.10.8",size="2m",
                          hostname="192.168.107.237",exportate="1M",
                          iperfpath="E:\iperf2\iperf.exe", interval=10,
                          serverip="192.168.9.79",logfile="F:/TMP/",
                          listingport="27141", username="root",
                          password="baicells", port=22):
        """
        support: udp/tcp
        iperf recive:linux server
        iperf send: windows control pc
        mode:stress
        """
        if mode == "UP":
            result = self._iperf_stress_upload(testmode,size,testtime,
                                               iperfpath,interval,serverip,
                                                listingport, username,password, port)
        else:
            result = self._iperf_stress_download(testmode,size, testtime,
                               iperfpath,interval,clientip,serverip,
                               listingport, username,password, port)
        if result:
            print "test ok"
        else:
            print "test fail"
        return result

    

"""
if __name__ == "__main__":
    test1 = TestPerformance()
    status=test1.delete_mme_gw("192.168.107.237",[['192.168.9.22'],['192.168.103.114']],0)
"""
