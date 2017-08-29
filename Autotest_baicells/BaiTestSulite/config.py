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

from ftplib import FTP
from xml.dom import  minidom

reload(sys) 
sys.setdefaultencoding('utf-8')


class GetConfig():
    '''Parsing XML-formatted files for multue test'''
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
        xml_labels = GetConfig.parsing_label_list(labelname, xmlfile)[0].split(" ")
        xml_elements_dict = {}
        for per_label in xml_labels:
            per_xml_label_list = GetConfig.parsing_label_list(per_label, xmlfile)
            xml_elements_dict[per_label] = per_xml_label_list[0]
        return xml_elements_dict

    @staticmethod
    def get_config(tcname, paraname):
        '''
	   Get the parameter instance of specific Test Case and Parameter.\n
	   tcname:  Test Case Name\n
	   paraname:	Parameter Name
        '''
        try:
	    fh = open('config.txt')
	    fc = fh.read() 
	    fh.close()
	except:
            print "config.text is read faild"
	fc = unicode(fc, 'utf-8')
	matchObj = re.match( r'(.*?)<TC=%s>(.*?)</TC>(.*)'%tcname, fc, re.M|re.S|re.I )
	if not matchObj:
	    print "Test Case not found: ", tcname
	if isinstance(tcname, unicode):
	    print "It's unicode." 
	    exit(5)
	tcconfig = matchObj.group(2)	
	matchObj = re.match( r'(.*?)<PARA=%s>(.*?)</PARA>(.*)'%paraname, tcconfig, re.M|re.S|re.I )
        if not matchObj:
	    print "Parameter not found" 
	    exit(6)
	paraconfig = matchObj.group(2)
        #print "Parameter: ", paraname, " Configuration: ", paraconfig
	if re.search( r'^\s+ENUM\s+.*', paraconfig):	###ENUM Type	
	    options = re.findall(r'ENUM(.*?)$',paraconfig,re.S)
	    print options
	    return  options[0].split(",")
        elif re.search(r'^\s+COMMAND\s+.*', paraconfig):
            test = re.findall(r'COMMAND(.*?)$',paraconfig,re.S)
            return test[0]	
	elif re.search( r'^\s+DIGIT\s+.*', paraconfig):						###DIGIT Type
	    result, number = re.subn(r'^\s+DIGIT\s+(.*)', r'\1', paraconfig)
	    result, number = re.subn(r'\s+', r' ', result)
	    result, number = re.subn(r'$', r' ', result)	
	    options = re.findall(r'([\'\"].*?[\'\"]) ', result)
	    #print options
	    reoptions = []
	    for option in options:
		expected = 1
		if re.search(r'\'.*\'', option):    #Single Quotes -> expected result:ok
		    option, number = re.subn(r'\'(.*?)\'', r'\1', option)
		    expected = 1
		elif re.search(r'\".*\"', option):  #Double Quotes -> expected result:ko
		    ption, number = re.subn(r'\"(.*?)\"', r'\1', option)
		    expected = 0;
		else:
		    print "wrong option format."
		    expected = 2
		option, number = re.subn(r'\s+', r'', option)
		option, number = re.subn(r'-+', r'-', option)		
		if re.search( r'^-*\d+$', option):
		    oneoption = []
		    oneoption.append(option)
		    oneoption.append(expected)
		    reoptions.append(oneoption);
		else:
		    matchObj = re.match(r'^(-*\d+)~(-*\d+)$',option)
		    if matchObj:
			for i in range(int(matchObj.group(1)), int(matchObj.group(2))+1):
			    oneoption = []
			    oneoption.append(i)
			   # oneoption.append(expected)
			    reoptions.append(oneoption)
            return reoptions	
	elif re.search( r'^\s+COMB\s+.*', paraconfig):						###LIST Type
	    result, number = re.subn(r'^\s+COMB\s+(.*)', r'\1', paraconfig)
	    result, number = re.subn(r'\s+', r' ', result)
	    result, number = re.subn(r'$', r' ', result)	
	    result, number = re.subn(r'\\\\', r'TAG0', result)
	    result, number = re.subn(r'\\\'', r'TAG1', result)
	    result, number = re.subn(r'\\\"', r'TAG2', result)
	    options = re.findall(r'([\'\"].*?[\'\"]) ', result)
	    reoptions = []
	    for option in options:
		expected = 1;
		if re.search(r'\'.*\'', option):    #Single Quotes -> expected result:ok
		    option, number = re.subn(r'\'(.*?)\'', r'\1', option)
		    expected = 1;
		elif re.search(r'\".*\"', option):  #Double Quotes -> expected result:ko
		    option, number = re.subn(r'\"(.*?)\"', r'\1', option)
		    expected = 0;
		else:
		    print "wrong option format."
		    expected = 2;		
		option, number = re.subn(r'TAG0', r'\\',  option)
		option, number = re.subn(r'TAG1', '\'',  option)
		option, number = re.subn(r'TAG2', '\"',  option)
		fields=option.split(',')
		#fields.append(expected)
		reoptions.append(fields)
	    return reoptions
	else:
	    print "Parameter format wrong." 
	    exit(7)

    @staticmethod
    def get_cpeiplist(ueargs):
        cpeiplist = []
        for ueinfo in ueargs:
            cpeiplist.append(ueinfo['cpeip'])
        return cpeiplist

    @staticmethod
    def get_ftpiplist(ueargs):
        ftpiplist=[]
        for ueinfo in ueargs:
            ftpiplist.append(ueinfo['serverip'])
        return ftpiplist

    @staticmethod
    def get_imsilist(ueargs):
        imsilist=[]
        for ueinfo in ueargs:
            imsilist.append(ueinfo['id'])
        return imsilist
    
'''xml预定义实体引用
&lt;	<	less than
&gt;	>	greater than
&amp;	&	ampersand
&apos;	'	apostrophe
&quot;	"	quotation mark
'''


