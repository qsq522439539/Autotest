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

from setup import *
from monitor import *
from runtest import *



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
MAILIST = ["lipeng-T@baicells.com"]
HOMEDIR = sys.path[0]

# cell route
CELLROTE= ["if route -n | grep -q 10.0.10.0;then :;else route add -net 10.0.10.0/24 gw 192.168.9.46;fi",
           "if route -n | grep -q 100.0.100.0;then : ;else route add -net 100.0.100.0/24 gw 192.168.9.56;fi",
           "if route -n | grep -q 123.1.1.0 ;then :;else route add -net 123.1.1.0/24 gw 192.168.9.57;fi"]

# FTP route
FTPROUTE1 = "route add -net 10.10.10.0/24 gw 192.168.9.42"
FTPROUTE2 = "ifconfig em1:ftp%s inet 123.1.1.%s netmask 255.255.255.255 up"


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


class Parsing_XML():
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
        ue_list=[]
        for node in ue_nodes: 
            ue_id = self.get_attrvalue(node,'id') 
            node_clientip = self.get_xmlnode(node,'cpeip')
            node_serverip = self.get_xmlnode(node, 'serverip')
            node_downfile = self.get_xmlnode(node,'downfile')
            node_localpath = self.get_xmlnode(node,'localpath')
            node_upfile = self.get_xmlnode(node, 'upfile')
            node_uppath = self.get_xmlnode(node, 'uppath')
            ue_clientip = self.get_nodevalue(node_clientip[0])
            ue_serverip = self.get_nodevalue(node_serverip[0])
            ue_downfile = self.get_nodevalue(node_downfile[0])
            ue_localpath = self.get_nodevalue(node_localpath[0]).encode('utf-8','ignore')
            ue_upfile = self.get_nodevalue(node_upfile[0])
            ue_uppath = self.get_nodevalue(node_uppath[0])
            ue = {}
            ue['id'],ue['cpeip'],ue['serverip'],ue['downfile'],ue['localpath'],ue["upfile"],ue["uppath"]= (
                ue_id,ue_clientip,ue_serverip,ue_downfile,ue_localpath,ue_upfile,ue_uppath)
            ue_list.append(ue)
        return ue_list

    @staticmethod
    def parsing_label_list(labelname, xmlfile):
        '''Parsing Gets the list labels'''
        try:
            xml_dom = xml.dom.minidom.parse(xmlfile)
            xml_label = xml_dom.getElementsByTagName(labelname)
        except IOError:
            print 'Failed to open %s file,Please check it' % xmlfile
            exit(1)
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

if __name__ == "__main__":
    if not os.path.exists("Result"):
        os.mkdir("Result")
    setloger()
    logger = logging.getLogger('test')
    ftpargs = Parsing_XML.specific_elements('comonlabel', 'args.xml')
    logger.info("Ftp args is %s " % ftpargs)
    parxml= Parsing_XML()
    ueargs= parxml.get_xml_data('args.xml')
    logger.info("UE args is %s " % ueargs)
    logger.info("Ftp setting start")
    imsilist = []
    cpeiplist = []
    ftpiplist = []
    for ueinfo in ueargs:
        imsilist.append(ueinfo["id"])
        cpeiplist.append(ueinfo['cpeip'])
        ftpiplist.append(ueinfo['serverip'])
   # do setup
    #open_root_permissions(ftpargs["chost"],ftpargs["adminpw"])
   # setcellroute(ftpargs["chost"])
    setfile()
    initdb(imsilist)
   # print celllist
    logger.info("Ftp test is start")
    app = QApplication(sys.argv)
    form = MainWindow(cpeiplist,ftpiplist,imsilist,ftpargs, ueargs)
    form.show()
    app.exec_()
