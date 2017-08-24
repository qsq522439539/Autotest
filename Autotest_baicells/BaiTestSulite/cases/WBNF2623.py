'''
    test case no: WB.NF.26.23
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
        self.logger.info("mmeips is %s" % self.mmeips)
        self.logger.info("kill mme1 process")
        job = TestPerformance()
        self.logger.info("add error gw")
        job.add_mme_egw(self.args["chost"],self.mmeerrorip,self.mmeips,0)
        test = LmtSeting("http://%s" %self.args["chost"])
        test.login_lmt()
        test.mmepool_enable_setting(ipseclist,mmelist,qslist[0])
        test.lgw_setting(["1","NAT"])
        test.do_reboot()
        test.tear_down()

    def _dotest(self):
        self.logger.info("check ue&cell status")
        test = LmtCheck("http://%s" % self.args["chost"])
        test.login_lmt()
        cellstatus = test.check_cell_state("Active")
        if not cellstatus:
            test.tear_down()
            return False
        mmestatus = test.check_mme_state("4")
        if not mmestatus:
            test.tear_down()
            return False
        test.tear_down()
        job = TestPerformance()
        job.cpe_ping_background(["192.168.9.79"])
        time.sleep(180)
        uenum_ping = job.cpe_ping_pass_num()
        if uenum_ping != "1":
            job.Signal.put("STOP")
            return False
        self.logger.info("delet error gw")
        job.delete_mme_gw(self.args["chost"],self.mmeips,0)
        time.sleep(60)
        self.logger.info("check ue&cell status")
        test = LmtCheck("http://%s" % self.args["chost"])
        test.login_lmt()
        cellstatus = test.check_cell_state("Active")
        if not cellstatus:
            test.tear_down()
            job.Signal.put("STOP")
            return False
        mmestatus = test.check_mme_state("2")
        if not mmestatus:
            test.tear_down()
            job.Signal.put("STOP")
            return False
        test.tear_down()
        self.logger.info("kill mme2 process")
        self.logger.info("add error gw")
        job.add_mme_egw(self.args["chost"],self.mmeerrorip,self.mmeips,1)
        self.logger.info("check mme status")
        time.sleep(30)
        test = LmtCheck("http://%s" % self.args["chost"])
        test.login_lmt()
        mmestatus = test.check_mme_state("3")
        if not mmestatus:
            test.tear_down()
            job.Signal.put("STOP")
            return False
        time.sleep(120)
        uenum_ping = job.cpe_ping_pass_num()
        if uenum_ping != "1":
            job.Signal.put("STOP")
            return False
        self.logger.info("start mme2")
        self.logger.info("delet error gw")
        job.delete_mme_gw(self.args["chost"],self.mmeips,0)
        self.logger.info("stop ping")
        job.Signal.put("STOP")
        return True
    
    def _runtest(self):
        self._setup()
        times = 1
        failtime = 0
        self._dotest()
        for i in range(times):
            self.logger.info("The No. %s test start" % i)
            status = self._dotest()
            if status:
                self.logger.info("The No. %s test pass" % i)
            else:
                self.logger.info("The No. %s test fail" % i)
                failtime +=1
        if failtime > 0:
            self.logger.error("WB.NF.26.23 is test Fail")
            return "Fail"
        else:
            self.logger.info("WB.NF.26.23 is test Pass")
            return "Pass"
        
        
        
        
    
                                  
        
        


        


	     

