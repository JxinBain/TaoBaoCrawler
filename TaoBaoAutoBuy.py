# -*- coding: utf-8 -*-
# @Time    : 2019/7/10 15:35
# @Author  : JxinBain
# @Email   : 843008493@qq.com
# @File    : ByWebDriver.py
# @Software: PyCharm

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from  pyquery import PyQuery as pq
import time
import logging
import pymongo
import os
import configparser

#   logging文件配置
logging.basicConfig(filename="TaobaoAutoBuy.log", filemode="w",
                    format="%(asctime)s %(name)s:%(levelname)s:%(message)s",
                    datefmt="%d-%M-%Y %H:%M:%S", level=logging.DEBUG)

mongo_url = 'localhost'
mongo_port = 27017
mongo_db = 'taobao'
mongo_table = 'taobao'
client = pymongo.MongoClient(mongo_url,mongo_port)
db = client[mongo_db]

class IniConfUtil:

    def __init__(self,file_name = 'cfg.ini'):
        #  初始化方法
        self.__cfg_path = file_name   # ini文件名
        if os.path.exists(self.__cfg_path):
            self.__conf = configparser.ConfigParser()        # 创建管理对象
            self.__conf.read(self.__cfg_path, encoding="utf-8")  # 读ini文件
        else:
            logging.error('配置文件不存在,请检查')


    def get_value(self,section,key):
        #   取值方法
        if self.__conf.has_option(section=section,option=key):
            return self.__conf.get(section=section,option=key)
        else:
            return None



class TaobaoSpider:

    def __init__(self,username,password,alipay_pwd):
        self.username = username
        self.password = password
        self.__options = webdriver.ChromeOptions()  # 此步骤很重要，设置为开发者模式，防止被各大网站识别出来使用了Selenium
        self.__options.add_experimental_option('excludeSwitches', ['enable-automation'])
        self.__driver = webdriver.Chrome(executable_path='chromedrive-handle', options=self.__options)
        self.__wait = WebDriverWait(self.__driver, 10)  # 由于加载页面是需要时间等待故引入时间等待；
        self.__login_url = 'https://login.taobao.com/member/login.jhtml'
        self.__index_url = 'https://www.taobao.com/'
        self.alipay_pwd = alipay_pwd

    def __redirect(self, url):
        self.__driver.get(url)

    def __get_element_clickable(self,by,tag):
        return self.__wait.until(EC.element_to_be_clickable((by, tag)))

    def __get_element_located(self,by,tag):
        return self.__wait.until(EC.presence_of_element_located((by, tag)))

    def __element_exist(self,by,tag):
        if by==By.ID:
            return self.__driver.find_element_by_id(tag).is_displayed()
        elif by==By.XPATH:
            return self.__driver.find_element_by_xpath(tag).is_displayed()
        elif by==By.NAME:
            return self.__driver.find_element_by_name(tag).is_displayed()
        elif by==By.CLASS_NAME:
            return self.__driver.find_element_by_class_name(tag).is_displayed()
        elif by==By.CSS_SELECTOR:
            return self.__driver.find_element_by_css_selector(tag).is_displayed()
        elif by ==By.LINK_TEXT:
            return self.__driver.find_element_by_link_text(tag).is_displayed()
        elif by==By.TAG_NAME:
            return self.__driver.find_element_by_tag_name(tag).is_displayed()
        else:
            return False

    def __switch_account_login(self):
        #   切换到帐号密码登录
        self.__get_element_clickable(By.ID, 'J_Quick2Static').click()

    def __input_account(self):
        #   输入帐号
        account_input = self.__get_element_located(By.ID, 'TPL_username_1')
        account_input.clear()
        account_input.send_keys(self.username)

    def __input_password(self):
        #   输入密码
        pwd_input = self.__get_element_located(By.ID, 'TPL_password_1')
        pwd_input.clear()
        pwd_input.send_keys(self.password)

    def __slider_item(self):
        # #   滑动滚动条
        # slider = self.__get_element_located(By.XPATH, "//*[@id='nc_1_n1z']")
        # # 平行移动鼠标
        # action = ActionChains(self.__driver)
        # action.drag_and_drop_by_offset(slider, 500, 0).perform()
        if self.__element_exist(By.XPATH,"//*[@id='nc_1_n1z']"):
            #   需要校验滚动条
            logging.debug('需要校验滚动条')
            #   滑动滚动条
            slider = self.__get_element_located(By.XPATH, "//*[@id='nc_1_n1z']")
            # 平行移动鼠标
            action = ActionChains(self.__driver)
            action.drag_and_drop_by_offset(slider, 500, 0).perform()
        else:
            #   不需要校验滚动条
            logging.debug('不需要校验滚动条')

    def __login_button_click(self):
        #   点击登录按钮
        self.__get_element_clickable(By.ID, 'J_SubmitStatic').click()

    def __login(self):
        try:
            self.__driver.get(self.__login_url)
            #   切换到帐号密码登录
            self.__switch_account_login()
            #   输入帐号
            self.__input_account()
            #   输入密码
            self.__input_password()
            #   点击登录按钮登录
            self.__login_button_click()
            while self.__driver.current_url==self.__login_url:
                #   输入密码
                self.__input_password()
                #   滑动滚动条
                self.__slider_item()
                #   点击登录按钮登录
                self.__login_button_click()
                time.sleep(2)
                # 检测是否登录完成
                if self.__driver.current_url!=self.__login_url:
                    break
            # self.__redirect(url=self.__index_url)  #   重新跳转到主页
            return True
        except Exception as e:
            logging.ERROR('登录出错:',e.__str__())
            logging.exception("Exception occurred")
            return False


    # 循环遍历加载浏览器
    def __next_page(self,page_number):
        try:
            # 模拟输入指定的页数
            input = self.__get_element_located(By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > input')
            # 确认提交按钮
            submit = self.__get_element_located(By.XPATH, '//*[@id="mainsrp-pager"]/div/div/div/div[2]/span[3]')
            input.clear()  # 清除input框中的信息
            input.send_keys(page_number)
            time.sleep(5)
            submit.click()
            # 用于判断输入的页数和跳转的页数是否相等
            self.__wait.until(EC.text_to_be_present_in_element(
                (By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > ul > li.item.active > span'), str(page_number)))
            self.__get_product_info()  # 判断成功调用
        except TimeoutError:
            return self.__next_page(page_number)

    def start(self):
        # 先登录
        if self.__login():
            logging.debug('登录成功')
            print(self.__driver.get_cookies())
            self.__get_element_clickable(By.ID,tag='mc-menu-hd').click()  # 点击购物车按钮,跳转到购物车页面
            self.__get_element_clickable(By.ID,tag='J_SelectAll1').click()  # 点击全选按钮,勾选全部商品
            time.sleep(2)
            self.__get_element_located(By.CLASS_NAME, 'submit-btn').click()  # 点击支付按钮,开始支付
            self.__get_element_located(By.CLASS_NAME, 'go-btn').click()  # 点击支付按钮,开始支付
            self.__get_element_located(By.CLASS_NAME, 'ui-form-explain') # 等待校验完成
            self.__get_element_located(By.ID,'payPassword_rsainput').send_keys(self.alipay_pwd)  # 输入支付宝密码
            self.__get_element_located(By.ID,'J_authSubmit').click()  # 输入密码
        else:
            # 登录失败
            pass

    def release_resouce(self):
        self.__driver.close()

def main():
    ini = IniConfUtil()
    username = ini.get_value('user','TaobaoAccount')   # 输入登录帐号
    pwd = ini.get_value('user','TaobaoPassword')    # 输入登录密码
    alipay_pwd = ini.get_value('user','AlipayPassword')
    if username and pwd and len(alipay_pwd)==6:
        taobao = TaobaoSpider(username=username.strip(), password=pwd.strip(),alipay_pwd = alipay_pwd.strip())
        taobao.start()
        time.sleep(100)
        taobao.release_resouce()
    else:
        input('配置文件异常')
        logging.error('配置文件异常')

if __name__ == '__main__':
    main()
