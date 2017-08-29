#coding=utf-8
import time
import logging

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from Selenium2Library import utils

from config import *

TIMEOUT=30


class WebSetKeyword():

    def __init__(self,address):
        self.driver = webdriver.Chrome()
        #打开浏览器
        self.driver.get(address)
        self.driver.maximize_window()
        self.logger = logging.getLogger('test')
        
    #定位元素
    def local_element_by_xpath(self,locator,timeout=TIMEOUT):
        for i in range(TIMEOUT):
            try:
                elem = WebDriverWait(self.driver, 1).until(
                    EC.presence_of_element_located((By.XPATH, locator)))
                element = WebDriverWait(self.driver,1).until(
                        EC.visibility_of(elem))
                return element
            except:
                time.sleep(1)
        self.logger.error("Wait by visibility_of %s faild"  % locator)
        return None
    
    #输入元素
    def element_input(self,locator,text,timeout=TIMEOUT):
        try:
            element = self.local_element_by_xpath(locator,timeout)
            element.clear()
            element.send_keys(text)
        except:
            return False
        
    #列表选择by label
    def select_from_list_by_label(self,locator,*labels):
        if not labels:
            self.logger.error("No value given.")
        items_str = "label(s) '%s' " % ",".join(labels)
        select = self._get_select_list(locator)
        for label in labels:
            select.select_by_visible_text(label)
            
    #列表选择by value
    def select_from_list_by_value(self,locator, *values):
        if not values:
            self.logger.error("No value given.")
        items_str = "value(s) '%s' " % ",".join(values)
        select = self._get_select_list(locator)
        for value in values:
            select.select_by_value(value)
    
    #等待弹窗出现
    def wait_until_alert_is_present(self,timeout=TIMEOUT,close=True):
        alert = WebDriverWait(self.driver,TIMEOUT).until(EC.alert_is_present())
        if close:
            alert.accept()
    
    #等待元素不可见
    def wait_until_element_not_visable(self,locator,timeout=TIMEOUT):
        def exit_element():
            try:
                elem = WebDriverWait(self.driver, 1).until(
                       EC.presence_of_element_located((By.XPATH, locator)))
                if elem.is_displayed():
                    return False
                else:
                    return True
            except:
                return True
        for n in range(int(timeout)):
            status = exit_element()
            if status:
                return
            else:
                time.sleep(3)
    
    #判断是否被选中
    def checkbox_selected_status(self,locator,timeout=TIMEOUT):
        element = self.local_element_by_xpath(locator,timeout)
        if element.is_selected():
            return "1"
        else:
            return "0"
    
    #通过select选项的索引来定位选择对应选项（从0开始计数），如选择第三个选项:select_by_index(2)
    def _get_select_list(self,locator):
        se = self.local_element_by_xpath(locator,TIMEOUT)
        return Select(se)
    
    #完成并开始回收初始化数据垃圾
    def tear_down(self):
        self.driver.close()
    
    #获取表格行数
    def get_table_rowcnt(self,locator,timeout):
        table = self.local_element_by_xpath(locator,timeout)
        if table is not None:
            table_rows = table.find_elements_by_tag_name("tr")
            return len(table_rows)
        else:
            return 0
    
    #获取表格
    def get_table_cells(self,locator,timeout):
        table = self.local_element_by_xpath(locator,timeout)
        cells = []
        if table is not None:
            rows = table.find_elements_by_xpath("./thead/tr")
            if len(rows) < 1:
                rows = table.find_elements_by_xpath("./tbody/tr")
            if len(rows) < 1:
                rows = table.find_elements_by_xpath("./tfoot/tr")
            for row in rows:
                columlist = []
                columns = row.find_elements_by_tag_name('th')
                if len(columns) < 1:
                    columns = row.find_elements_by_tag_name('td')
                for column in columns:  
                    columlist.append(column.text)
                cells.append(columlist)
            return cells
        return None
    
    #获取文本
    def get_text(self,locator,timeout=TIMEOUT):
        return self.local_element_by_xpath(locator,timeout).text
    
    #获取值
    def get_value(self,locator,timeout=TIMEOUT):
        element = self.local_element_by_xpath(locator,timeout)
        return element.get_attribute('value') if element is not None else None
    
    #等待元素可以被点击
    def wait_until_element_is_clickable(self,locator, timeout=TIMEOUT):
        element = WebDriverWait(self.driver, timeout).until(
                  EC.element_to_be_clickable((By.XPATH,locator)))

    # about lmt   
    def login_lmt(self):
        self.element_input("//*[@id='password']","admin",TIMEOUT)
        self.local_element_by_xpath("//*[@id='log_button']",TIMEOUT).click()
        #self.local_element_by_xpath("//*[@id='header_login']/div[3]/span/input",TIMEOUT).click()
    
    #重启
    def do_reboot(self):
        self.local_element_by_xpath("//*[@id='Loki_reboot']",TIMEOUT).click()
        self.local_element_by_xpath("//*[@id='reboot_button']",TIMEOUT).click()
        self.wait_until_element_not_visable("//*[@id='wait_icon']/img",300)
    
    #接受弹窗
    def accept_alert(self,num):
        for i in range(num):
            self.wait_until_alert_is_present(TIMEOUT,True)
        self.wait_until_element_not_visable("//*[@id='wait_icon']/img",TIMEOUT)

    # about cpe
    def login_cpe(self):
        self.element_input("//*[@id='inner']/table/tbody/tr[2]/td[2]/input","admin",TIMEOUT)
        self.element_input("//*[@id='inner']/table/tbody/tr[3]/td[2]/input","admin",TIMEOUT)
        self.local_element_by_xpath("//*[@id='inner']/table/tbody/tr[4]/td[1]/input",TIMEOUT).click()

   # about omc
    def login_omc(self,ifid,user,passwd):
        self.element_input("//*[@id='uid']",user,TIMEOUT)
        self.element_input("//*[@id='password']",passwd,TIMEOUT)
        self.local_element_by_xpath("//*[@id='loginfrom']/div[4]",TIMEOUT).click()
        self.driver.switch_to_frame(ifid)

    def omc_switch_boss(self,boss):
        self.local_element_by_xpath("//*[@id='arrow']",TIMEOUT).click()
        self.local_element_by_xpath("//*[@id='nav_bar_user_pop']/div/span",TIMEOUT).click()
        self.element_input("//*[@id='operatorCode']",boss,TIMEOUT)
        self.local_element_by_xpath("//*[@id='toolbar_tableChangeOperatorList']/div/img",TIMEOUT).click()
        time.sleep(3)
        self.local_element_by_xpath("//*[@id='datagrid-row-r4-2-0']/td[3]/div",TIMEOUT).click()
        self.local_element_by_xpath("//*[@id='changeOperator']/div[2]/div/div/a[1]/span",TIMEOUT).click()


class LmtSeting(WebSetKeyword):

    # quick setting 
    def quick_setting(self,sets,MMEPOOL=False):
        self.local_element_by_xpath("//*[@id='my_menu']/div[1]/a[2]",TIMEOUT).click()
        self.select_from_list_by_label("//*[@id='LTE_BANDS_SUPPORTED']",sets[0])
        self.select_from_list_by_label("//*[@id='LTE_DL_BANDWIDTH']",sets[1])
        self.select_from_list_by_value("//*[@id='LTE_DL_EARFCN']",sets[2])
        self.select_from_list_by_value("//*[@id='LTE_TDD_SUBFRAME_ASSIGNMENT']",sets[3])
        self.select_from_list_by_value("//*[@id='LTE_TDD_SPECIAL_SUB_FRAME_PATTERNS']",sets[4])
        self.element_input("//*[@id='LTE_PHY_CELLID_LIST']",sets[5])
        self.element_input("//*[@id='LTE_CELL_IDENTITY']",sets[6])
        if not MMEPOOL:
            mmeipnum =  self.get_table_rowcnt("//*[@id='right_subnet_table']",TIMEOUT)
            for i in range(mmeipnum - 1):
                self.local_element_by_xpath("//*[@id='right_subnet_table']/tbody/tr[2]/td[2]/input",TIMEOUT).click()
                self.accept_alert(1)
            self.element_input("//*[@id='LTE_SIGLINK_SERVER_LIST']",sets[7])
            self.local_element_by_xpath("//*[@id='mmeip_add_button']",TIMEOUT).click()
        self.element_input("//*[@id='LTE_OAM_PLMNID']",sets[8])
        self.element_input("//*[@id='LTE_TAC']",sets[9])
        self.local_element_by_xpath("//*[@id='save_button']",TIMEOUT).click()
        self.accept_alert(1)

    # LGW setting
    def lgw_setting(self,sets):
        self.local_element_by_xpath("//*[@id='my_menu']/div[3]/a[5]",TIMEOUT).click()
        self.select_from_list_by_value("//*[@id='LTE_LGW_SWITCH']",sets[0])
        if sets[1] != "":
            self.select_from_list_by_label("//*[@id='LTE_LGW_TRANSFER_MODE']",sets[1])
        self.local_element_by_xpath("//*[@id='save_button']",TIMEOUT).click()
        self.accept_alert(1)

    def lgw_ippool_setting(self,sets):
        self.local_element_by_xpath("//*[@id='my_menu']/div[3]/a[5]",TIMEOUT).click()
        self.element_input("//*[@id='LTE_LGW_START_UE_ADDR']",sets[0])
        self.select_from_list_by_value("//*[@id='LTE_LGW_NET_MASK']",sets[1])
        self.local_element_by_xpath("//*[@id='save_button']",TIMEOUT).click()
        self.accept_alert(1)

    def lgw_imsi_binding(self,imsilist,ipset):
        self.local_element_by_xpath("//*[@id='my_menu']/div[3]/a[5]",TIMEOUT).click()
        self.select_from_list_by_value("//*[@id='LTE_LGW_STATIC_IP_ADDR_SWITCH']","1")
        self.element_input("//*[@id='LTE_LGW_FIRST_STATIC_IP_ADDRESS']",ipset[0])
        self.element_input("//*[@id='LTE_LGW_LAST_STATIC_IP_ADDRESS']",ipset[1])
        imsitable = self.get_table_cells("//*[@id='right_subnet_table']",TIMEOUT)
        #移除MMEIP
        if imsitable is not None:
            for i in range(len(imsitable)-1):
                self.local_element_by_xpath("//*[@id='right_subnet_table']/tbody/tr[2]/td[2]/input",TIMEOUT).click()
        p = ipset[0].split(".")[-1]
        ip = ipset[0].split["."]
        for n,imsi in enumerate(imsilist):
            self.element_input("//*[@id='imsi']",imsi)         
            ip[-1]= str(p)
            ip = ".".join(ip)
            self.element_input("//*[@id='ip']",ip)
            self.local_element_by_xpath("//*[@id='imsiip_add_button']",TIMEOUT).click()
            p = int(p) + 1
        self.local_element_by_xpath("//*[@id='save_button']",TIMEOUT).click()
        self.accept_alert(1)

    # cloudepc setting
    def cloudepc_setting(self,status):
        _local_epc="//*[@id='TOGGLE_SWITCH']"
        self.local_element_by_xpath("//*[@id='my_menu']/div[1]/a[2]",TIMEOUT).click()
        statusnow = self.get_value(_local_epc,TIMEOUT)
        if status != statusnow:
            self.select_from_list_by_value(_local_epc,status)
            self.local_element_by_xpath("//*[@id='save_button']",TIMEOUT).click()
            self.accept_alert(1)

    # ipsec  enable setting
    def ipsec_enable_setting(self,status):
        self.local_element_by_xpath("//*[@id='my_menu']/div[3]/a[4]",TIMEOUT).click()
        statusnow = self.checkbox_selected_status("//*[@id='ipsec_enabled']",TIMEOUT)
        print statusnow
        if status != statusnow:
            self.local_element_by_xpath("//*[@id='ipsec_enabled']",TIMEOUT).click()
            self.local_element_by_xpath("//*[@id='save_ipsec']",TIMEOUT).click()
            self.accept_alert(1)

    # sync setting
    def sysc_enable_setting(self,status):
        self.local_element_by_xpath("//*[@id='my_menu']/div[4]/a[3]",TIMEOUT).click()
        status_gps = self.get_value("//*[@id='LTE_GPS_SYNC_ENABLE']",TIMEOUT)
        status_1588 = self.get_value("//*[@id='LTE_1588_SYNC_ENABLE']",TIMEOUT)
        SAVA=False
        if status_gps != status:
            self.select_from_list_by_value("//*[@id='LTE_GPS_SYNC_ENABLE']",status)
            SAVE=True
        if status_1588 != status:
            self.select_from_list_by_value("//*[@id='LTE_1588_SYNC_ENABLE']",status)
            SAVE=True
        if SAVE:
            self.local_element_by_xpath("//*[@id='save_button']",TIMEOUT).click()
            self.accept_alert(1)

    # ipsec tunnel setting       
    def _ipsec_tunnel_edit(self,ipseclist,ADD=False):
        self.select_from_list_by_value("//*[@id='ipsec_tunnel_enabled']",ipseclist[0])
        self.element_input("//*[@id='ipsec_tunnel_name']",ipseclist[1],TIMEOUT)
        self.element_input("//*[@id='ipsec_tunnel_ip']",ipseclist[2],TIMEOUT)
        rightsubnum = self.get_table_rowcnt("//*[@id='right_subnet_table']",TIMEOUT)
        if rightsubnum > 1 and not ADD: 
            for i in range(rightsubnum - 1):
                self.local_element_by_xpath("//*[@id='right_subnet_table']/tbody/tr[2]/td[2]/input",TIMEOUT).click()
                self.accept_alert(1)
        self.element_input("//*[@id='ipsec_rightsubnet_add_ip']",ipseclist[3],TIMEOUT)
        self.element_input("//*[@id='ipsec_rightsubnet_add_mask']",ipseclist[4],TIMEOUT)
        self.local_element_by_xpath("//*[@id='ipsec_rightsubnet_add_button']",TIMEOUT).click()
        self.select_from_list_by_value("//*[@id='tunnel_authby']",ipseclist[5])
        self.element_input("//*[@id='ipsec_tunnel_pre_shared_key']",ipseclist[6],TIMEOUT)
        self.local_element_by_xpath("//*[@id='save_tunnel']",TIMEOUT).click()
        if not ADD:
            self.accept_alert(1)
        else:
            self.accept_alert(2)
   
    def ipsec_tunnel_setting(self,tunnellist):
        self.local_element_by_xpath("//*[@id='my_menu']/div[3]/a[4]",TIMEOUT).click()
        ipsecnum = self.get_table_rowcnt("//*[@id='ipsec_tunnel_table']",TIMEOUT) - 1
        if len(tunnellist) < 2:
            mmepoolstatus = self.get_value("//*[@id='LTE_MMEPOOL_ENABLE']",TIMEOUT)
            if mmepoolstatus == "1":
                self.mmepool_disable_setting()
            if ipsecnum > 1:
                # delete second ipsec
                self.local_element_by_xpath("//*[@id='ipsec_tunnel_table']/tbody/tr[3]/td[7]/input",TIMEOUT).click()
                self.accept_alert(1)
                self.wait_until_element_not_visable("//*[@id='wait_txt']",60)
            # edit first ipsec
            self.local_element_by_xpath("//*[@id='ipsec_tunnel_table']/tbody/tr[2]/td[6]/input",60).click()
            self._ipsec_tunnel_edit(tunnellist[0])
        else:
            if ipsecnum > 1:
                # edit first ipsec
                self.local_element_by_xpath("//*[@id='ipsec_tunnel_table']/tbody/tr[2]/td[6]/input",TIMEOUT).click()
                self._ipsec_tunnel_edit(tunnellist[0])
                # edit second ipsec
                time.sleep(1)
                self.local_element_by_xpath("//*[@id='ipsec_tunnel_table']/tbody/tr[3]/td[6]/input",TIMEOUT).click()
                self._ipsec_tunnel_edit(tunnellist[1])
            else:
                # edit first ipsec
                self.local_element_by_xpath("//*[@id='ipsec_tunnel_table']/tbody/tr[2]/td[6]/input",TIMEOUT).click()
                self._ipsec_tunnel_edit(tunnellist[0])
                # add second ipsec
                time.sleep(1)
                self.local_element_by_xpath("//*[@id='ipsec_new_tunnel']",TIMEOUT).click()
                self._ipsec_tunnel_edit(tunnellist[1],True)
            
    # mmepool disbale setting
    def mmepool_disable_setting(self):
        self.local_element_by_xpath("//*[@id='my_menu']/div[3]/a[4]",TIMEOUT).click()
        statusnow = self.get_value("//*[@id='LTE_MMEPOOL_ENABLE']",TIMEOUT)
        if statusnow == "0":
            self.logger.info("Mmepool enable is %s" % statusnow)
            return True
        else:
            self.select_from_list_by_value("//*[@id='LTE_MMEPOOL_ENABLE']","0")
            self.local_element_by_xpath("//*[@id='save_mmepool']",TIMEOUT).click()
            self.accept_alert(2)

    # mmepool enable setting  
    def mmepool_enable_setting(self,ipseclist,mmelist,qssets):
        # disable cloud epc
        self.cloudepc_setting("0")
        self.quick_setting(qssets,True)
        # enabel ipsec
        self.ipsec_enable_setting("1")
        # disabel mmepool
        self.mmepool_disable_setting()
        # add two ipsec
        self.ipsec_tunnel_setting(ipseclist)
        self.select_from_list_by_value("//*[@id='LTE_MMEPOOL_ENABLE']","1")
        mmeip1 = self.get_table_rowcnt("//*[@id='mmepool_1_table']",TIMEOUT)
        if mmeip1 > 1:
            for i in range(mmeip1-1):
                self.local_element_by_xpath("//*[@id='mmepool_1_table']/tbody/tr[2]/td[2]/input",TIMEOUT).click()
                self.accept_alert(1)
        self.element_input("//*[@id='LTE_MMEPOOL_IP_LIST']",mmelist[0][0],TIMEOUT)
        self.local_element_by_xpath("//*[@id='mmeip1_add_button']",TIMEOUT).click()
        mmeip2 = self.get_table_rowcnt("//*[@id='mmepool_2_table']",TIMEOUT)
        if mmeip2 > 1:
            for i in range(mmeip2-1):
                self.local_element_by_xpath("//*[@id='mmepool_2_table']/tbody/tr[2]/td[2]/input",TIMEOUT).click()
                self.accept_alert(1)
        self.element_input("//*[@id='LTE_MMEPOOL_IP_LIST2']",mmelist[1][0],TIMEOUT)
        self.local_element_by_xpath("//*[@id='mmeip2_add_button']",TIMEOUT).click()
        ipsec1 = self.get_text("//*[@id='ipsec_tunnel_table']/tbody/tr[2]/td[2]",TIMEOUT)
        ipsec2 = self.get_text("//*[@id='ipsec_tunnel_table']/tbody/tr[3]/td[2]",TIMEOUT)
        self.select_from_list_by_value("//*[@id='bind_if_name']",ipsec1)
        self.select_from_list_by_value("//*[@id='bind_if_name2']",ipsec2)
        self.local_element_by_xpath("//*[@id='save_mmepool']",TIMEOUT).click()
        self.accept_alert(1)

    def capacity_parameters_setting(self,status):
        self.local_element_by_xpath("//*[@id='my_menu']/div[5]/a[5]",TIMEOUT).click()
        self.local_element_by_xpath("//*[@id='stateBut11']",TIMEOUT).click()
        status_now = self.get_value("//*[@id='LTE_96_UE_ENABLE']",TIMEOUT)
        if status_now != status:
            self.select_from_list_by_value("//*[@id='LTE_96_UE_ENABLE']",status)
            self.local_element_by_xpath("//*[@id='save_button']",TIMEOUT).click()
            self.accept_alert(1)
        else:
            return

    def cpe_webenable_setting(self):
        self.local_element_by_xpath("//*[@id='a24']",TIMEOUT).click()
        self.local_element_by_xpath("//*[@id='a35']",TIMEOUT).click()
        self.driver.switch_to_frame("mainifr")
        status1 = self.checkbox_selected_status("//*[@id='https_enable']",TIMEOUT)
        status2 = self.checkbox_selected_status("//*[@id='https_wan']",TIMEOUT)
        CHANGE=False
        if status1 != "1":
            self.local_element_by_xpath("//*[@id='https_enable']",TIMEOUT).click()
            CHANGE=True
        if status2 != "1":
            self.local_element_by_xpath("//*[@id='https_wan']",TIMEOUT).click()
            CHANGE=True
        if CHANGE:
            self.local_element_by_xpath("//*[@id='submit']/span/span/span",TIMEOUT).click()
            self.wait_until_alert_is_present(TIMEOUT,True)
            self.wait_until_element_not_visable("/html/body/form/p/img",300)

    def linkkeepalive_setting(self,status,minute):
        self.local_element_by_xpath("//*[@id='my_menu']/div[5]/a[5]",TIMEOUT).click()
        self.local_element_by_xpath("//*[@id='stateBut15']",TIMEOUT).click()
        status1 = self.get_value("//*[@id='LTE_WAN_CHECK_ENABLE']",TIMEOUT)
        status2 = self.get_value("//*[@id='LTE_WAN_CHECK_TIMER_LEN']",TIMEOUT)
        CHANGE=False
        if status1 != status:
            self.select_from_list_by_value("//*[@id='LTE_WAN_CHECK_ENABLE']",status)
            CHANGE=True
        if status2 != minute:
            self.select_from_list_by_value("//*[@id='LTE_WAN_CHECK_TIMER_LEN']",minute)
            CHANGE=True
        if CHANGE:
            self.local_element_by_xpath("//*[@id='save_button']",TIMEOUT).click()
            self.accept_alert(1)
        return

    # OMC setting
    def omc_setting(self,omcurl):
        self.local_element_by_xpath("//*[@id='my_menu']/div[4]/a[2]",TIMEOUT).click()
        omcnow = self.get_value("//*[@id='MANAGEMENT_SERVER']",TIMEOUT)
        if omcnow != omcurl:
            self.element_input("//*[@id='MANAGEMENT_SERVER']",omcurl,TIMEOUT)
            self.element_input("//*[@id='cloudkey']","",TIMEOUT)
            self.local_element_by_xpath("//*[@id='save_button']",TIMEOUT).click()
            self.accept_alert(1)
        return
        
class OmcSeting(WebSetKeyword):
    def add_kpi_template(self,group,kpiname,kpilist):
        self.local_element_by_xpath("//*[@id='body_div']/ul/li[6]/a",TIMEOUT).click()
        self.local_element_by_xpath("//*[@id='body_div']/ul/li[6]/ul/li[1]/a/span",TIMEOUT).click()
        self.local_element_by_xpath("//*[@id='temp_normal_title']/ul/li[2]/a",TIMEOUT).click()
        self.local_element_by_xpath("//*//*[@id='newAddMenu']/div[2]/div[1]",TIMEOUT).click()
        self.element_input("//*[@id='addTemplateGroupName']",group,TIMEOUT)
        self.local_element_by_xpath("//*[@id='winAddTemplateGroup']/div/div[2]/div/div/a[1]/span",TIMEOUT).click()
        self.local_element_by_xpath("//*[@id='temp_normal_title']/ul/li[2]/a",TIMEOUT).click()
        self.local_element_by_xpath("//*[@id='newAddMenu']/div[4]/div[1]",TIMEOUT).click()
        self.element_input("//*[@id='addCustomQueryName']",kpiname,TIMEOUT).click()
        self.select_from_list_by_value("//*[@id='winCustomQueryTemplate']/div/div/div/div[1]/div/div[2]/span/input[1]",group)
        self.local_element_by_xpath("//*[@id='_easyui_tree_35']/span[4]",TIMEOUT).click()
        self.local_element_by_xpath("//*[@id='datagrid-row-r45-2-2']/td[2]/div",TIMEOUT).click()
        self.local_element_by_xpath("//*[@id='datagrid-row-r45-2-9']/td[2]/div",TIMEOUT).click()
        self.local_element_by_xpath("//*[@id='datagrid-row-r45-2-37']/td[2]/div",TIMEOUT).click()
        self.local_element_by_xpath("//*[@id='winCustomQueryTemplate']/div/div/div/div[2]/div/div/div[2]/div/a[1]",TIMEOUT).click()
        self.local_element_by_xpath("//*[@id='winCustomQueryTemplate']/div/div/div/div[3]/div/div/a[1]/span",TIMEOUT).click()

    def omc_report_setting(self,minute,cellsn):
        self.local_element_by_xpath("//*[@id='body_div']/ul/li[6]/a/span",TIMEOUT).click()
        self.local_element_by_xpath("//*[@id='body_div']/ul/li[6]/ul/li[2]/a/span",TIMEOUT).click()
        self.select_from_list_by_value("//*[@id='mainpage']/div/div[1]/div[2]/div[1]/div[2]/span/input[1]",minute)
        self.element_input("//*[@id='Measurement_Customization_Search_Text']",cellsn,TIMEOUT)
        self.local_element_by_xpath("//*[@id='toolbar_GridCell_Measurement_Customization']/div/img",TIMEOUT).click()
        status = self.checkbox_selected_status("//*[@id='datagrid-row-r4-2-0']/td[1]/div/input",TIMEOUT)
        if status != "1":
            self.local_element_by_xpath("//*[@id='datagrid-row-r4-2-0']/td[4]/div",TIMEOUT).click()
        self.local_element_by_xpath("//*[@id='mainpage']/div/div[1]/div[2]/a/span",TIMEOUT).click()

    def omc_atach_set(self,sn,ON):
        self.local_element_by_xpath("//*[@id='body_div']/ul/li[2]/a",TIMEOUT).click()
        self.local_element_by_xpath("//*[@id='body_div']/ul/li[2]/ul/li[2]/a/span",TIMEOUT).click()
        self.element_input("//*[@id='commonQueryText']",sn,TIMEOUT)
        self.local_element_by_xpath("//*[@id='toolbar_GridCell_cellParam']/div/div[2]/img",TIMEOUT).click()
        self.local_element_by_xpath("//*[@id='datagrid-row-r4-2-0']/td[3]/div/div",TIMEOUT).click()
        if ON:
            self.element_input("//*[@id='showParamValues']/div[1]/div[2]/span/input[1]","ACT CELL",TIMEOUT)
            self.local_element_by_xpath("//*[@id='showParamValues']/div[1]/div[2]/span/span/a",TIMEOUT).click()
            time.sleep(3)
            self.local_element_by_xpath("//*[@id='showParamValues']/div[1]/div[2]/div/a[1]/span",TIMEOUT).click()
        else:
            self.element_input("//*[@id='showParamValues']/div[1]/div[2]/span/input[1]","DEACT CELL",TIMEOUT)
            self.local_element_by_xpath("//*[@id='showParamValues']/div[1]/div[2]/span/span/a",TIMEOUT).click()
            time.sleep(3)
            self.local_element_by_xpath("//*[@id='showParamValues']/div[1]/div[2]/div/a[1]/span",TIMEOUT).click()
        

class OmcCheck(WebSetKeyword):
    def omc_check_perf(self,cellsn,):
        self.local_element_by_xpath("//*[@id='body_div']/ul/li[6]/a/span",TIMEOUT).click()
        self.local_element_by_xpath("//*[@id='body_div']/ul/li[6]/ul/li[1]/a/span",TIMEOUT).click()
        self.local_element_by_xpath("//*[@id='kpiTemplateTreeGrid']/ul/li[6]/a",TIMEOUT).click()
        self.local_element_by_xpath("//*[@id='kpiTemplateTreeGrid']/ul/li[6]/ul/li/a/span",TIMEOUT).click()
        self.local_element_by_xpath("//*[@id='customQueryTreeChildMenu']/div[2]/div[1]",TIMEOUT).click()
        self.element_input("//*[@id='eNodeB_Search_Text']",cellsn,TIMEOUT)
        self.local_element_by_xpath("//*[@id='toolbar_eNodeBDataGrid']/div/img",TIMEOUT).click()
        self.local_element_by_xpath("//*[@id='datagrid-row-r10-2-0']/td[7]/div/span[1]/span",TIMEOUT).click()
        self.wait_until_element_not_visable("//*[@id='winTableClick']/div[2]/div/div/div/div[4]",120)
        time.sleep(240)
        resulttable = self.get_table_cells("//*[@id='winTableClick']/div[2]/div/div/div/div[1]/div[2]/div[2]/table",TIMEOUT)
        return resulttable

    
class LmtCheck(WebSetKeyword):
    def _check_state(self,locator,timeout, *texts):
        for i in range(int(timeout)):
            element = self.local_element_by_xpath(locator,3)
            current = element.text
            for expect in texts:
                if expect == current:
                    return None
            time.sleep(10)
        return current
        
    def check_cell_state(self,*texts):
        checkstatus = self._check_state("//*[@id='LTE_RFTX_OP_STATE']",TIMEOUT,*texts)
        if checkstatus == None:
            self.logger.info("cell's state is expectd")
            return True
        else:
            self.logger.error("cell's state is unexpect, its %s" % checkstatus)
            return False

    def check_ipsec_state(self,*texts):
        checkstatus = self._check_state("//*[@id='ipsec_status']",TIMEOUT,*texts)
        if checkstatus == None:
            self.logger.info("ipsec's state is expectd")
            return True
        else:
            self.logger.error("ipsec's state is unexpect, its %s" % checkstatus)
            return False

    def check_ue_state(self,uenum):
        checkstatus = self._check_state("//*[@id='UE_COUNT']",TIMEOUT,uenum)
        if checkstatus == None:
            self.logger.info("Ue count is expectd")
            return True
        else:
            return False

    def check_mme_state(self,expect):
        """
        0:mme unconnectd
        1:mme connectd
        2:mme1 and mme2 connectd
        3:mme1 connectd mme2 unconnectd
        4:mme1 unconectd mme2 connectd
        5.mme1 and mme2 unconnectd
        """
        if expect == "0":
            status = self._check_state("//*[@id='MME_STATUS']",TIMEOUT,"Not Connected",u"未连接")
            if status == None:
                self.logger.info("mme's is unconnectd")
                return True
            else:
                self.logger.error("mme's is unexpectd, its %s" % status)
                return False
        elif expect == "1":
            status = self._check_state("//*[@id='MME_STATUS']",TIMEOUT,"Connected",u"已连接")
            if status == None:
                self.logger.info("mme is connectd")
                return True
            else:
                self.logger.error("mme is unexpectd, its %s" % status)
                return False
        elif expect == "2":
            status1 = self._check_state("//*[@id='MME1_STATUS']",TIMEOUT,"Connected",u"已连接")
            status2 = self._check_state("//*[@id='MME2_STATUS']",TIMEOUT,"Connected",u"已连接")
            if status1 == None and status2 == None:
                self.logger.info("mme1 and mme2 is all connectd")
                return True
            else:
                self.logger.error("mme is unexpectd,mme1 is %s,mme2 is %s" %(status1,status2))
                return False
        elif expect == "3":
            status1 = self._check_state("//*[@id='MME1_STATUS']",TIMEOUT,"Connected",u"已连接")
            status2 = self._check_state("//*[@id='MME2_STATUS']",TIMEOUT,"Not Connected",u"未连接")
            if status1 == None and status2 == None:
                self.logger.info("mme1 is connected, mme2 is not connected")
                return True
            else:
                self.logger.error("mme is unexpectd,mme1 is %s,mme2 is %s" %(status1,status2))
                return False
        elif expect == "4":
            status1 = self._check_state("//*[@id='MME1_STATUS']",TIMEOUT,"Not Connected",u"未连接")
            status2 = self._check_state("//*[@id='MME2_STATUS']",TIMEOUT,"Connected",u"已连接")
            if status1 == None and status2 == None:
                self.logger.info("mme1 is not connected, mme2 is connected")
                return True
            else:
                self.logger.error("mme is unexpectd,mme1 is %s,mme2 is %s" %(status1,status2))
                return False
        elif expect == "5":
            status1 = self._check_state("//*[@id='MME1_STATUS']",TIMEOUT,"Not Connected",u"未连接")
            status2 = self._check_state("//*[@id='MME2_STATUS']",TIMEOUT,"Not Connected",u"未连接")
            if status1 == None and status2 == None:
                self.logger.info("mme1 and mme2 is all not connectd")
                return True
            else:
                self.logger.error("mme is unexpectd,mme1 is %s,mme2 is %s" %(status1,status2))
                return False
        else:
            self.logger.error("%s in unknow args" % expect)
            return False

    def capacity_parameters_check(self,status):
        self.local_element_by_xpath("//*[@id='my_menu']/div[5]/a[5]",TIMEOUT).click()
        self.local_element_by_xpath("//*[@id='stateBut11']",TIMEOUT).click()
        status_now = self.get_value("//*[@id='LTE_96_UE_ENABLE']",TIMEOUT)
        if status_now == status:
            return True
        else:
            return False

    def ue_count_check(self):
        self.local_element_by_xpath("//*[@id='my_menu']/div[1]/a[1]",TIMEOUT).click()
        return self.get_value("//*[@id='UE_COUNT']",TIMEOUT)

    def get_ue_ip_list(self):
        self.local_element_by_xpath("//*[@id='my_menu']/div[1]/a[1]",TIMEOUT).click()
        cells = self.get_table_cells("//*[@id='UE_table']",TIMEOUT)
        iplist = []
        for cell in cells[1:]:
            iplist.append(cell[4])
        return iplist

    def get_ue_imsi_list(self):
        self.local_element_by_xpath("//*[@id='my_menu']/div[1]/a[1]",TIMEOUT).click()
        cells = self.get_table_cells("//*[@id='UE_table']",TIMEOUT)
        imsilist = {}
        for cell in cells[1:]:
            imsilist[cell[2]] = cell[4]
        return imsilist

    def get_ue_imsimac_list(self):
        self.local_element_by_xpath("//*[@id='my_menu']/div[1]/a[1]",TIMEOUT).click()
        cells = self.get_table_cells("//*[@id='UE_table']",TIMEOUT)
        imsilist = {}
        for cell in cells[1:]:
            imsilist[cell[2]] = cell[3]
        return imsilist


"""
ipseclist = GetConfig.get_config("MMEPOOL", "TWOTUNNEL")
mmelist = GetConfig.get_config("MMEPOOL", "MMEPOOLIP")
qslist = GetConfig.get_config("MMEPOOL", "QSMMEPOOL1")
print ipseclist
print mmelist
test = LmtSeting("http://192.168.107.237")
test.login_lmt()
test.mmepool_enable_setting(ipseclist,mmelist,qslist[0])
test.do_reboot()
test.tear_down()
test = LmtCheck("http://192.168.9.42")
test.login_lmt()
test.get_ue_ip_list()
"""


     

    
    
