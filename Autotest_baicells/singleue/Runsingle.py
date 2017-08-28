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

from PyQt4.Qt import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import QtGui, QtCore

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email import Encoders
from multiprocessing import Process
from ftplib import FTP
from optparse import OptionParser
from xml.dom import  minidom


reload(sys) 
sys.setdefaultencoding('utf-8')

LGWMODELIST = {
	"NAT": "0",
	"ROUTER": "1",
	"BRIDGE": "2"}

SETLGWCMD = "cli -c 'oam.set LTE_LGW_TRANSFER_MODE %s'"
SETSACMD = "cli -c 'oam.set LTE_TDD_SUBFRAME_ASSIGNMENT %s'"
SETSPCMD = "cli -c 'oam.set LTE_TDD_SPECIAL_SUB_FRAME_PATTERNS %s'"
GETLGWCMD = "cli -c 'oam.getwild LTE_LGW_TRANSFER_MODE' | awk -F ' ' '{print $2}'  | tr -d '\n'"
GETSACMD = "cli -c 'oam.getwild LTE_TDD_SUBFRAME_ASSIGNMENT' | awk -F' ' '{print $2}' | tr -d '\n'"
GETSPCMD = "cli -c 'oam.getwild LTE_TDD_SPECIAL_SUB_FRAME_PATTERNS' | awk -F' ' '{print $2}' | tr -d '\n'"
ISOTIMEFORMAT='%Y-%m-%d-%X'
MAILIST = ["lipeng-T@baicells.com","zangmingming@baicells.com","gaohanjian@baicells.com"]
HOMEDIR = sys.path[0]

# cell route
CELLROTE= ["if route -n  | grep -q 192.168.9.46;then :;else route add -net 10.0.10.0/24 gw 192.168.9.46;fi",
		   "if route -n  | grep -q 192.168.9.56;then :;else route add -net 100.0.100.0/24 gw 192.168.9.56;fi",
		   "if route -n  | grep -q 192.168.9.76;then :;else route add -net 124.1.1.0/24 gw 192.168.9.76;fi"]

# FTP route
FTPROUTE1 = "route add -net 10.10.10.0/24 gw 192.168.9.42"
FTPROUTE2 = "ifconfig em1:ftp%s inet 124.1.1.%s netmask 255.255.255.255 up"




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
		root = doc.documentElement #读取xml
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
			xml_dom = xml.dom.minidom.parse(xmlfile) #打开xml文档
			xml_label = xml_dom.getElementsByTagName(labelname) #获得子标签
		except IOError:
			print ('Failed to open %s file,Please check it' % xmlfile)
		xml_label_list = []
		for single_label in xml_label:
			xml_label_list.append(single_label.firstChild.data)#获取元素第一个子节点的数据
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

	def splitpath(self,remotepath):
		try:
			position=remotepath.rfind('/')
			return (remotepath[:position+1],remotepath[position+1:])
		except:
			return
		
	def download(self,starttime,testtime,host,username,password,remotepath,localpath):
		#connect to the FTP Server and check the return
		try:
			res = self.ConnectFTP(host,username,password)
			if(res[0]!=1):
				return "ERROR1"
			ftp=res[1]
			dires = self.splitpath(remotepath)
		except:
			pass
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
			remote=self.splitpath(remotepath)
		except:
			return "ERROR1"
		try:
			ftp.cwd(remote[0])
		except:
			pass
		try:
			rsize=ftp.size(remote[1])
		except:
			rsize = 0
		try:
			lsize=os.stat(localpath).st_size
			if lsize == rsize:
				ftp.delete(remote[1])
			rsize=ftp.size(remote[1])
			if (rsize==None):
				rsize=0L
			localf=open(localpath,'rb')
			if rsize < lsize:
				localf.seek(rsize)
			ftp.voidcmd('TYPE I')
			datasock=''
			esize=''
		except:
			return "ERROR2"
		try:
			datasock,esize=ftp.ntransfercmd("STOR "+remote[1],rsize)
		except Exception, e:
			self.logger.error('----------ftp.ntransfercmd-------- : %s' % e)
			return "ERROR2"
		while True:
			try:
				buf=localf.read(1024 * 1024)
				if not len(buf):
					return
				if time.time() - starttime < testtime:
					datasock.sendall(buf)
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

	def repair(self,host):
		try:
			for cmd in CELLROTE:
				status = do_clicmd(host, cmd)
				if status == "":
					self.logger.info("CELL set route sucessfull")
				else:
					self.logger.error("%s CELL set route fail" % host)
			return
		except:
			return

	def _Download_FTP(self,chost,alert,testtime, remotepath,localpath,
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
		self.logger.info("%s start down load time on %s" %( host,starttime))
		while True:
				if time.time() - starttime > testtime:
					break
				#status = self._downftp(starttime,testtime,host,username,password,remotepath,localpath)
				status = self.download(starttime, testtime,host,username,password,remotepath,localpath)
				if status is "ERROR1":
					self.logger.error("%s ftp connect failed" % host)
					self.sendalert(alert,"ftperror", host)
					time.sleep(60)
					self.repair(chost)
				elif status is "ERROR2":
					self.logger.info("%s ftp download Interrupt" % host)
					self.sendalert(alert,"dlerror", host)
					time.sleep(60)
					self.repair(chost)
		return True

	def _Upload_FTP(self,chost, alert,testtime, remotepath,localpath,
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
			#status = self._upftp(starttime,testtime,host,username,password,remotepath,localpath,callback=None)
			status = self.upload(starttime,testtime,host,username,password,remotepath,
				localpath)
			if status is "ERROR1":
				self.logger.error("%s ftp connect failed" %host )
				self.sendalert(alert,"ftperror", host)
				time.sleep(60)
				self.repair(chost)
			elif status is "ERROR2":
				self. logger.error("%s ftp start error"%host)
				self.sendalert(alert,"ulerror", host)
				time.sleep(60)
				self.repair(chost)
			elif status is "ERROR3":
				self.logger.error("%s ftp upload Interrupt" %host)
				self.sendalert(alert,"ulerror", host)
				time.sleep(60)
				self.repair(chost)
		return True

	def dogetrate(self,alert,expectspeed,hostname,username, password, port):
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
					totalrate = str(rate[0]) + str(rate[1])
					totalrate = totalrate * 1024 * 1024
					if totalrate < expectspeed:
						self.logger.error("Total rate is lower than expected")
						self.sendalert(alert,"ratelow")
					return rate
			else:
				return ["null","null"]
		except:
			return ["null","null"]
			return False

		#Save syslog rate
		
	def syslog_save_rate(self,celllist,alert,expectspeed,testtime,username, password, port):
		port = int(port)
		time.sleep(5)
		testtime = int(testtime)
		# if os.path.exists(logfile):
		#    os.remove(logfile)
		for hostname in celllist:
			logfile="Result/%s.csv" % hostname
			f = open(logfile, 'a')
			f.write('Time, UL_Rate, DL_Rate\n')
			f.close()
		starttime = time.time()
		while time.time() - starttime < testtime:
			ullist = []
			dllist = []
			for hostname in celllist:
				logfile="Result/%s.csv" % hostname
				status = self.dogetrate(alert,expectspeed,hostname,username, password, port)
				if not status:
					self.logger.error("%s rate get faild" % hostname)
				else:
					try:
						f = open(logfile, 'a')
						f.write('%s, %s, %s\n' % (time.strftime('%Y:%m:%d:%H:%M:%S'),status[0], status[1]))
						f.close()
						ullist.append(status[0])
						dllist.append(status[1])
					except:
						pass
			try:
				s = shelve.open('rate.db')
				s["ul"] = ullist
				s["dl"] = dllist
				s.close()
			except:
				pass
			time.sleep(20)
		return
		# check syslog rate

	def getcpuload(self,hostname,username, password, port):
		try:
			client=paramiko.SSHClient()
			client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
			client.connect(hostname, port, username, password)
			stdin,stdout,stderr=client.exec_command("uptime | awk -F age: '{print $2}' | awk -F, '{print $1}' | tr -d ' \n'")
			load=stdout.read()
			client.close()
			return load
		except:
			return None
		
	def cell_check_load(self,celllist,testtime,hostname,username, password, port):
		port = int(port)
		testtime = int(testtime)
		# if os.path.exists("Result/cpuload.csv"):
	   #     os.remove("Result/cpuload.csv")
		starttime = time.time()
		f = open("Result/cpuload.csv", 'a')
		f.write('Cell, Time, Cpuload\n')
		while time.time() - starttime < testtime:
			loadlist = []
			for cell in celllist:
				load = self.getcpuload(cell,username,password, port)
				if load is None:
					loadlist.append("0.00")
				else:
					loadlist.append(load)
				try:
					f = open("Result/cpuload.csv", 'a')
					f.write('%s,%s, %s\n'%(cell,time.strftime('%Y:%m:%d:%H:%M:%S',time.localtime(time.time())),load))
					f.close()
				except:
					pass
			try:
				s = shelve.open('load.db')
				s["load"] = loadlist
				s.close()
			except:
				pass
			time.sleep(300)
		return
	
		# FTP stress
	def Ftp_Stresstest(self,dolist,inputargs, ftpargs, ueargs):
		expectspeed = self._getnumbits("1M")
		testtime = int(inputargs["testtime"])
		loadthreads = []
		iplist = []
		celllist = []
		allcell = ftpargs["dotest"].split(" ")
		# download thread create
		for num in dolist:
			idnum = allcell[num]
			for i in range(int(inputargs["download"])):
				downthread = threading.Thread(target=self._Download_FTP,
											  name="downloadftp%s"%i,
											  args=(
												ftpargs["chost"],inputargs["alarm"],
												inputargs["testtime"],
												ueargs[idnum]["downfile"],
												ueargs[idnum]["localpath"],
												ueargs[idnum]["serverip"],
												ftpargs["ftpuser"],
												ftpargs["ftppw"]))
				loadthreads.append(downthread)
			celllist.append(ueargs[idnum]["clientip"])
			iplist.append(ueargs[idnum]["serverip"])
			
		# upload thread create
		for num in dolist:
			idnum = allcell[num]
			for i in range(int(inputargs["upload"])):
				upthread = threading.Thread(target=self._Upload_FTP,
											name = "upload%s"%i,
											args=(ftpargs["chost"],inputargs["alarm"],
											  testtime,
											  ueargs[idnum]["upfile"],
											  ueargs[idnum]["uppath"],
											  ueargs[idnum]["serverip"],
											  ftpargs["ftpuser"],
											  ftpargs["ftppw"]))
				loadthreads.append(upthread)

		ratecheck = threading.Thread(target=self.syslog_save_rate,
									 name="getrate",
									 args=(celllist,inputargs["alarm"],
										   expectspeed,testtime,
										   "root","root123","27149"))
		ratecheck.setDaemon(True)
		ratecheck.start()
		pingcheck = threading.Thread(target=self._ping_check,
									 name = "pingcheck",
									 args=(inputargs["alarm"],iplist,5))
		loadcheck = threading.Thread(target=self.cell_check_load,
									name = "loadcheck",
									args=(celllist,testtime,
										  ftpargs["chost"],
										  "root",
										  "root123",
										  "27149"))
		loadcheck.setDaemon(True)
		loadcheck.start()
		pingcheck.setDaemon(True)
		pingcheck.start()
		for n,thread in enumerate(loadthreads):
			thread.setDaemon(True)
			thread.start()
			self.logger.info("The %s ue test thread start" % n)
		for thread in loadthreads:
			thread.join()
		self.sendalert(inputargs["alarm"],"Result")
		self.logger.info("Ftp test finsish")
		return
		
	def _ping_check(self,alert,iplist, count):
		while True:
			pinglist = []
			for ip in iplist:
				status = self._ping(ip, count)
				if status:
					self.logger.info("%s is ping ok" % ip)
					pinglist.append("Pass")
				else:
					self.logger.error("%s is ping fail" % ip)
					self.sendalert(alert,"pingerror",ip)
					pinglist.append("Fail")
			try:
				s = shelve.open('ping.db')
				s["ping"] = pinglist
				s.close()
			except:
				pass
			time.sleep(300)

	def _ping(self, ip, count):
		REPATH = re.compile(r'TTL')
		cmd = "ping %s -n %s -w 10" %(ip, count)
		try:
			p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
			while p.poll() is None:
				buff = p.stdout.readline()
				if REPATH.findall(buff):
					return True
			return False
		except:
			return False
			
	def _playmp3(self,mfile):
		clip = mp3play.load(mfile)
		clip.play()
		self.logger.info("Play music")
		time.sleep(min(30, clip.seconds()))
		clip.stop()
		return

	def sendalert(self,alarttype,error,host="",mfile="123.mp3"): #告警方式
		if alarttype is "V": #音乐
			pass
		# music = threading.Thread(target=self._playmp3,name="music",args=("123.mp3",))
		# music.start()
		elif alarttype is "M": #邮件
			mail = threading.Thread(target=self.send_mail,name="mail",args=(host,error))
			mail.start()
		elif alarttype is "A": #都有
			pass
			#music = threading.Thread(target=self._playmp3,name="music",args=("123.mp3"))
			#music.start()
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
		self.logger.info("mail send ok")
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
	parser.add_option("-e", "--K/M", dest="expectrate",
					 help="Expectd rate of total.\
						   default: 10M.")
	parser.add_option("-l","--NAT/ROUTER/BRIDGE", dest="lgwmode",
					  help="LGW mode:NAT/ROUTER/BRIDGE.\
						   default: NAT.")
	parser.add_option("-s","--1/2", dest="subframe",
					  help="SubFrame Assignment:1/2.\
						   default: 2.")
	parser.add_option("-p","--5/7", dest="sspframe",
					  help="Special SubFrame Patterns:5/7.\
						   default: 7.")
	parser.add_option("-a","--V/M/A", dest="alarm",
					  help="Alarm type，support:V(voice)/M(mail)/A(all)\
						   default:V")
	(options, args) = parser.parse_args()
	test_args = {}
	if options.download is None:
		options.download = "1"
	if options.upload is None:
		options.upload = "1"
	if options.testtime is None:
		options.testtime = "90"
	if options.expectrate is None:
		options.expectrate = "5M"
	if options.lgwmode is None:
		options.lgwmode = "NAT"
	if options.subframe is None:
		options.subframe = "2"
	if options.sspframe is None:
		options.sspframe = "7"
	if options.alarm is None:
		options.alarm = "V"
	test_args["download"] = options.download
	test_args["upload"] = options.upload
	test_args["testtime"] = options.testtime
	test_args["expectrate"] = options.expectrate
	test_args["lgwmode"] = options.lgwmode
	test_args["subframe"] = options.subframe
	test_args["sspframe"] = options.sspframe
	test_args["alarm"] = options.alarm
	return test_args

def setloger():
	logger = logging.getLogger('test')
	logger.setLevel(logging.DEBUG) #日志等级debug，等级低的不会输出
	#创建一个handler，用于写入日志文件
	fh = logging.FileHandler('Result/testlog.txt')
	fh.setLevel(logging.DEBUG)
	#再创建一个handler，用于输出到控制台
	ch = logging.StreamHandler()
	ch.setLevel(logging.WARNING)
	formatter = logging.Formatter('%(asctime)s - %(name)s -%(levelname)s - %(message)s')
	#定义handler的输出格式（formatter）
	fh.setFormatter(formatter)
	ch.setFormatter(formatter)
	#给logger添加handler
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

def setting(inputargs, ftpargs):
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
	return

	
class CheckWindow(QtGui.QWidget):
	def __init__(self,iplist):
		super(CheckWindow, self).__init__()
		self.iplist = iplist
		self.items = len(self.iplist)
		self.setWindowTitle(u"业务测试监控(Baicells)")
		self.resize(900,600)
		palette1 = QtGui.QPalette()
		palette1.setColor(self.backgroundRole(), QColor("#F0E68C"))
		self.setPalette(palette1)
		self.setAutoFillBackground(True)
		
		self.gridlayout = QtGui.QGridLayout()
		self.gridlayout.setSpacing(0)
		
		self.input0 = QLineEdit(self)
		self.input0.setReadOnly(True)
		self.input0.setText(u'CELL')
		self.input0.setAlignment(QtCore.Qt.AlignCenter)
		self.gridlayout.addWidget(self.input0, 0, 0)

		self.input1 = QLineEdit(self)
		self.input1.setText(u'PING')
		self.input1.setAlignment(QtCore.Qt.AlignCenter)
		self.input1.setReadOnly(True)
		self.gridlayout.addWidget(self.input1, 0, 1)

		self.input2 = QLineEdit(self)
		self.input2.setText(u'UL速率(Mbps)')
		self.input2.setAlignment(QtCore.Qt.AlignCenter)
		self.input2.setReadOnly(True)
		self.gridlayout.addWidget(self.input2, 0, 2)

		self.input3 = QLineEdit(self)
		self.input3.setText(u'DL速率(Mpbs)')
		self.input3.setAlignment(QtCore.Qt.AlignCenter)
		self.input3.setReadOnly(True)
		self.gridlayout.addWidget(self.input3, 0, 3)

		self.input4 = QLineEdit(self)
		self.input4.setText(u'CPU负载')
		self.input4.setAlignment(QtCore.Qt.AlignCenter)
		self.input4.setReadOnly(True)
		self.gridlayout.addWidget(self.input4, 0, 4)

		self.setip()
		self.setping()
		self.setul()
		self.setdl()
		self.setcpu()

		self.setLayout(self.gridlayout)

	def setip(self):
		num = 1
		for ip in self.iplist:
			self.inputip = QLineEdit(self)
			self.inputip.setText(ip)
			self.inputip.setReadOnly(True)
			self.gridlayout.addWidget(self.inputip, num, 0)
			num += 1

	def setping(self):
		num = 1
		self.pinglist = []
		for i in range(self.items):
			self.inputp = QLineEdit(self)
			self.gridlayout.addWidget(self.inputp,num,1)
			num += 1
			self.pinglist.append(self.inputp)

	def setul(self):
		num = 1
		self.ullist = []
		for i in range(self.items):
			self.inputu = QLineEdit(self)
			self.gridlayout.addWidget(self.inputu,num,2)
			num += 1
			self.ullist.append(self.inputu)

	def setdl(self):
		num = 1
		self.dllist = []
		for i in range(self.items):
			self.inputd = QLineEdit(self)
			self.gridlayout.addWidget(self.inputd,num,3)
			num += 1
			self.dllist.append(self.inputd)

	def setcpu(self):
		num = 1
		self.cpulist = []
		for i in range(self.items):
			self.inputcpu = QLineEdit(self)
			self.gridlayout.addWidget(self.inputcpu,num,4)
			num += 1
			self.cpulist.append(self.inputcpu)
		
	def handleDisplay_ping(self, data):
		data = data.split(" ")
		for i, value in enumerate(self.pinglist):
			value.setText(data[i])

	def handleDisplay_ul(self,data):
		data = data.split(" ")
		for i, value in enumerate(self.ullist):
			value.setText(data[i])
			
	def handleDisplay_dl(self,data):
		data = data.split(" ")
		for i, value in enumerate(self.dllist):
			value.setText(data[i])

	def handleDisplay_cpu(self,data):
		data = data.split(" ")
		for i, value in enumerate(self.cpulist):
			value.setText(data[i])

			
class Backend_ping(QThread):
	update_date = pyqtSignal(QString)
	def run(self):
		while True:
			try:
				s = shelve.open('ping.db')
				values = s['ping']
				s.close()
				values = ' '.join(values)
			except:
				pass
			self.update_date.emit(QString(values))
			time.sleep(3)
			

class Backend_ul(QThread):
	update_date = pyqtSignal(QString)
	def run(self):
		while True:
			try:
				s = shelve.open('rate.db')
				values = s['ul']
				s.close()
				values = ' '.join(values)
			except:
				pass
			self.update_date.emit(QString(values))
			time.sleep(10)


class Backend_dl(QThread):
	update_date = pyqtSignal(QString)
	def run(self):
		while True:
			try:
				s = shelve.open('rate.db')
				values = s['dl']
				s.close()
				values = ' '.join(values)
			except:
				pass
			self.update_date.emit(QString(values))
			time.sleep(10)


class Backend_cpu(QThread):
	update_date = pyqtSignal(QString)
	def run(self):
		while True:
			try:
				s = shelve.open('load.db')
				values = s['load']
				s.close()
				values = ' '.join(values)
			except:
				pass
			self.update_date.emit(QString(values))
			time.sleep(10)

def initdb(celllist):
	if os.path.exists("rate.db"):
		os.remove("rate.db")
	if os.path.exists("ping.db"):
		os.remove("ping.db")
	if os.path.exists("load.db"):
		os.remove("load.db")
	ping = []
	ul = []
	dl = []
	load = []
	for cell in celllist:
		ul.append("0.00")
		dl.append("0.00")
		ping.append("Pass")
		load.append("0.00")
	s = shelve.open('rate.db')
	s["ul"] = ul
	s["dl"] = dl
	s.close()
	s = shelve.open('ping.db')
	s["ping"] = ping
	s.close()
	s = shelve.open('load.db')
	s["load"] = load
	s.close()


class MainWindow(QDialog):

	def __init__(self, celllist,ftpargs, ueargs):
		super(MainWindow, self).__init__()
		self.celllist = celllist
		self.argstemp = []
		self.dolist = []
		self.ftpargs = ftpargs
		self.ueargs = ueargs
		self.setWindowTitle(u"业务测试启动")
		self.resize(500, 650)
		palette1 = QtGui.QPalette()
		palette1.setColor(self.backgroundRole(), QColor("#6495ED"))
		self.setPalette(palette1)
		self.setAutoFillBackground(True)
		self.createlabel()
		self.createcheckbox()
		self.createbutton()
		self.Layout()

	def createlabel(self):
		self.titlelabel = QLabel(self.tr("Cell List:"))
		self.argslabel = QLabel(self.tr("Args Set:"))
		self.label_0 = QLabel(self.tr(u"UL Threads"))
		self.label_1 = QLabel(self.tr(u"DL Threads"))
		self.label_2 = QLabel(self.tr(u"Test Time(sec)"))
		self.edit0 = QtGui.QLineEdit()
		self.edit1 = QtGui.QLineEdit()
		self.edit2 = QtGui.QLineEdit()

	def createcheckbox(self):
		self.cellbox = []
		id_ = 0
		for cell in self.celllist:
			self.checkbox = QtGui.QCheckBox(u'%s' % cell,self)
			self.checkbox.value = id_
			self.checkbox.cell = cell
			self.checkbox.stateChanged.connect(self.checks)
			self.cellbox.append(self.checkbox)
			id_ += 1

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
		self.defaultbutton = QtGui.QPushButton(u"默认")
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
		n = 0
		for cell in self.cellbox:
			n+=1
			baseLayout.addWidget(cell,n ,0)
		baseLayout.addWidget(self.argslabel, n+1,0)
		baseLayout.addWidget(self.label_0, n+2,0)
		baseLayout.addWidget(self.label_1, n+3,0)
		baseLayout.addWidget(self.label_2, n+4,0)
		baseLayout.addWidget(self.edit0, n+2,1)
		baseLayout.addWidget(self.edit1, n+3,1)
		baseLayout.addWidget(self.edit2, n+4,1)
		
		footer1Layout = QHBoxLayout()
		acer1 = QtGui.QSpacerItem(10,30)
		acer2 = QtGui.QSpacerItem(20,10)

		footer2Layout = QHBoxLayout()
		footer1Layout.addWidget(self.helpbutton)
		footer1Layout.addWidget(self.defaultbutton)
		baseLayout.addItem(acer1, n+5,0)
		baseLayout.addItem(acer2, n+5,1)
		footer2Layout.addWidget(self.setallbutton)
		footer2Layout.addWidget(self.setbutton)

		baseLayout.setSizeConstraint(QLayout.SetFixedSize)
		baseLayout.setSpacing(10)
		baseLayout.addLayout(footer1Layout,n+5,0)
		baseLayout.addLayout(footer2Layout,n+5,3)
		self.setLayout(baseLayout)


	def Ondefault(self):
		pass

	def Onhelp(self):
		self.checkwin.show()
		
	def Onstart(self):
		inputargs = {}
		inputargs["upload"] = self.edit0.text()
		inputargs["download"] = self.edit1.text()
		inputargs["testtime"] = self.edit2.text()
		inputargs["alarm"] = "A"
		initdb(self.dolist)
		dotest = TestThread(self.argstemp,inputargs,self.ftpargs, self.ueargs)
		dotest.start()
		self.setbutton.setText(u"测试中")
		self.checkwin = CheckWindow(self.dolist)
		self.p = Backend_ping()
		self.u = Backend_ul()
		self.d = Backend_dl()
		self.c = Backend_cpu()
		self.p.update_date.connect(self.checkwin.handleDisplay_ping)
		self.u.update_date.connect(self.checkwin.handleDisplay_ul)
		self.d.update_date.connect(self.checkwin.handleDisplay_dl)
		self.c.update_date.connect(self.checkwin.handleDisplay_cpu)
		self.p.start()
		self.u.start()
		self.d.start()
		self.c.start()

	def Onsetall(self):
		self.checkbox_css4.setChecked(True)
		self.checkbox_acid3.setChecked(True)
		self.checkbox_v8test.setChecked(True)
		self.checkbox_octane.setChecked(True)
		self.checkbox_html5.setChecked(True)
		self.checkbox_dromaeo.setChecked(True)

class TestThread(QThread):

	def __init__(self,argstemp,inputtargs,ftpargs,ueargs):
		QThread.__init__(self)
		self.argstemp = argstemp
		self.inputtargs = inputtargs
		self.ftpargs = ftpargs
		self.ueargs = ueargs
		
	def run(self):
		testjob = FtpStress()
		testjob.Ftp_Stresstest(self.argstemp,self.inputtargs,self.ftpargs,self.ueargs)

def settestroute(celllist, ftpargs):
	"""setup before test"""
	# set cell route
	for host in celllist:
		for cmd in CELLROTE:
			status = do_clicmd(ftpargs["chost"], cmd)
			if status == "" or status == "pass":
				logger.info("%s CELL set route sucessfull" % host)
			else:
				logger.error("%s CELL set route fail" % host)

	"""
	# set ftpserver
	ftpstatus =""
	ftpstatus = do_clicmd(ftpargs["fhost"],FTPROUTE1,"root",
						  ftpargs["fsshpw"],22)
	for i in range(8):
		i += 1
		cmd = FTPROUTE2 % (i,i)
		ftpstatus = do_clicmd(ftpargs["fhost"],cmd,"root",
							  ftpargs["fsshpw"],22)
	if ftpstatus is "":
		logger.info("FTPserver set route sucessfull")
	else:
		logger.error("FTPserver set route fail")
	"""
	return None
	
if __name__ == "__main__":
	#创建result文件夹
	if not os.path.exists("Result"):
		os.mkdir("Result")
	#日志记录
	setloger()
	logger = logging.getLogger('test')
	#返回xml文件各个标签的值(字典形式) fhost:192.168.9.76
	ftpargs = Parsing_XML.specific_elements('comonlabel', 'args.xml')
	logger.info("Ftp args is %s " % ftpargs)
	parxml= Parsing_XML()
	#字典里又一个字典  {id:{clientip:192.168.9.37}}
	ueargs= parxml.get_xml_data('args.xml')
	logger.info("UE args is %s " % ueargs)
	logger.info("Ftp setting start")
	dolist = ftpargs["dotest"].split(" ")
	#clientip
	celllist = []
	for idnum in dolist:
		celllist.append(ueargs[idnum]["clientip"])
	#加路由
	settestroute(celllist, ftpargs)
	logger.info("Ftp test is start")
	app = QApplication(sys.argv)
	form = MainWindow(celllist,ftpargs, ueargs)
	form.show()
	app.exec_()
	
