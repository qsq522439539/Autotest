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
import xlrd
import logging

from xlutils.copy import copy

reload(sys) 
sys.setdefaultencoding('utf-8')
XLSNAME='TestList.xls'


class ParXls:
    def __init__(self):
        self.logger = logging.getLogger('test')
        
    def _open_xls(self):
        if not os.path.exists(XLSNAME):
            print "%s is not exist" % XLSNAME
            exit(0)
        try:
            workbook = xlrd.open_workbook(XLSNAME)
            return workbook
        except:
            print "%s is read faild" % XLSNAME
            exit(0)

    def _gettestlist(self):
        """
        dotestlist:
        {u'WB.PF.38': [2, 3],
         u'WB.PF.42': [6, 3],
         u'WB.PF.40': [4, 3],}
        """
        dotestlist ={}
        caseinfo = []
        workbook = self._open_xls()
        table = workbook.sheet_by_index(0)
        casestatus = table.col_values(2)[1:]
        caselist = table.col_values(1)[1:]
        for num,case in enumerate(caselist):
            if casestatus[num] == "On":
                caseinfo = [num+1,3]
                dotestlist[case] = caseinfo
        return dotestlist

    def _write_xls(self,result):
        """
            resultlist:
            [2, 3,"Pass"]
        """
        workbook = self._open_xls()
        table = copy(workbook)
        wtable = table.get_sheet(0)
        wtable.write(int(result[0]),int(result[1]),result[2])
        table.save(XLSNAME)
