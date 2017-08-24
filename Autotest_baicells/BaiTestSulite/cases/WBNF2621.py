'''
    test case no: WB.NF.26.21
    test setup: MMEPOOL open;
                cell active,mme connect
                SA2,SSP7 20M NAT
'''
import os
import logging
from common import *
from webset import *
from config import *

class DoTest():
    def __init__(self,args,ueargs):
        self.args = args
        self.ueargs = ueargs
        self.logger = logging.getLogger('test')
        self.logger.info("Args is %s" % self.args)
        self.logger.info("Ue args is %s" % self.ueargs)
    
    def _setup(self):
        '''
         Setup before starting test
        '''
        self.cpeiplist = GetConfig.get_cpeiplist(self.ueargs)
        self.logger.info("cpeiplist is %s " % self.cpeiplist)
        self.ftpiplist = GetConfig.get_ftpiplist(self.ueargs)
        self.logger.info("ftpiplist is %s" % self.ftpiplist)
        self.logger.info("mmepool enable setting")
        ipseclist = GetConfig.get_config("MMEPOOL","TWOTUNNEL")
        self.logger.info("ipseclist is %s" % ipseclist)
        mmelist = GetConfig.get_config("MMEPOOL","MMEPOOLIP")
        self.logger.info("mmelist is %s" % mmelist)
        qslist = GetConfig.get_config("MMEPOOL","QSMMEPOOL37")
        self.logger.info("qseting args is %s" % qslist)
        self.mmeerrorip = GetConfig.get_config("MMEPOOL","MMEERRORROUTE")
        self.mmeips = GetConfig.get_config("MMEPOOL","MMEIPS")
        test = LmtSeting("http://%s" %self.args["chost"])
        test.login_lmt()
        test.mmepool_enable_setting(ipseclist,mmelist,qslist[0])
        test.lgw_setting(["1","NAT"])
        test.do_reboot()
        test.tear_down()

    def _dotest(self,index):
        self.logger.info("check ue&cell status")
        test = LmtCheck("http://%s" % self.args["chost"])
        test.login_lmt()
        cellstatus = test.check_cell_state("Active")
        if not cellstatus:
            test.tear_down()
            return False
        mmestatus = test.check_mme_state("2")
        if not mmestatus:
            test.tear_down()
            return False
        test.tear_down()
        # set mme1 down
        job = TestPerformance()
        job.cpe_ping_background(["192.168.9.79"])
        uenum_ping = job.cpe_ping_pass_num()
        if uenum_ping != "1":
            return False
        self.logger.info("add error gw")
        job.add_mme_egw(self.args["chost"],self.mmeerrorip,self.mmeips,int(index))
        time.sleep(10)
        self.logger.info("check ue&cell status")
        test = LmtCheck("http://%s" % self.args["chost"])
        test.login_lmt()
        cellstatus = test.check_cell_state("Active")
        if not cellstatus:
            test.tear_down()
            return False
        mmestatus = test.check_mme_state(str(4-int(index)))
        if not mmestatus:
            test.tear_down()
            return False
        test.tear_down()
        check_stcp = job.check_epc_sctp(self.args["chost"],self.mmeips,int(index)+1)
        if check_stcp:
            self.logger.info("check mme sctp pass")
        else:
            self.logger.info("check mme sctp fail")
            return False
        uenum_ping = job.cpe_ping_pass_num()
        if uenum_ping != "1":
            return False
        # set mme up
        self.logger.info("delet error gw")
        job.delete_mme_gw(self.args["chost"],self.mmeips,int(index))
        time.sleep(10)
        self.logger.info("check ue&cell status")
        test = LmtCheck("http://%s" % self.args["chost"])
        test.login_lmt()
        cellstatus = test.check_cell_state("Active")
        if not cellstatus:
            test.tear_down()
            return False
        mmestatus = test.check_mme_state("2")
        if not mmestatus:
            test.tear_down()
            return False
        test.tear_down()
        # set ipsec down
        self.logger.info("set ipsec tunnel down")
        cell_ipsec_errorgw = self.args["chost"][:-1] + "100"
        ipsec1down = job._dosshcmd(self.args["chost"],27149,"route add -host %s gw %s" % (self.ipsecips[int(index)][0],cell_ipsec_errorgw),
                                   "root123",True)
        if not ipsec1down:
            self.logger.error("ipsec add error route fail")
            return False
        self.logger.info("check ue&cell status")
        test = LmtCheck("http://%s" % self.args["chost"])
        test.login_lmt()
        cellstatus = test.check_cell_state("Active")
        if not cellstatus:
            test.tear_down()
            return False
        mmestatus = test.check_mme_state(str(4-int(index)))
        if not mmestatus:
            test.tear_down()
            return False
        test.tear_down()
        uenum_ping = job.cpe_ping_pass_num()
        if uenum_ping != "1":
            return False
        # set ipsec up
                self.logger.info("set ipsec tunnel down")
        cell_ipsec_errorgw = self.args["chost"][:-1] + "100"
        ipsec1down = job._dosshcmd(self.args["chost"],27149,"route del -host %s " % self.ipsecips[index][0],
                                   "root123",True)
        if not ipsec1down:
            self.logger.error("ipsec add error route fail")
            return False
        self.logger.info("check ue&cell status")
        test = LmtCheck("http://%s" % self.args["chost"])
        test.login_lmt()
        cellstatus = test.check_cell_state("Active")
        if not cellstatus:
            test.tear_down()
            return False
        mmestatus = test.check_mme_state("2")
        if not mmestatus:
            test.tear_down()
            return False
        test.tear_down()
        uenum_ping = job.cpe_ping_pass_num()
        if uenum_ping != "1":
            return False
        self.logger.info("stop ping")
        job.Signal.put("STOP")  
        return True
    
    def _runtest(self):
        self._dotest()
        for i in range(2):
            self.logger.info("The %s mme&ipsec test start" % i)
            status = self._dotest(i)
            if status:
                self.logger.info("WB.NF.26.22 is test Pass")
                return "Pass"            
            else:
                self.logger.error("WB.NF.26.22 is test Fail")
                return "Fail"  
        
        
    
                                  
        
        


        


	     

