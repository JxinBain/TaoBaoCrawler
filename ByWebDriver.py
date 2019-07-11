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
import re

#   logging文件配置
logging.basicConfig(filename="TaobaoSpider.log", filemode="w",
                    format="%(asctime)s %(name)s:%(levelname)s:%(message)s",
                    datefmt="%d-%M-%Y %H:%M:%S", level=logging.DEBUG)

mongo_url = 'localhost'
mongo_port = 27017
mongo_db = 'taobao'
mongo_table = 'taobao'
client = pymongo.MongoClient(mongo_url,mongo_port)
db = client[mongo_db]


#   下一页 class = 'J_Ajax num icon-tag's

class TaobaoSpider:

    def __init__(self,username,password,product):
        self.username = username
        self.password = password
        self.product = product
        self.__options = webdriver.ChromeOptions()  # 此步骤很重要，设置为开发者模式，防止被各大网站识别出来使用了Selenium
        self.__options.add_experimental_option('excludeSwitches', ['enable-automation'])
        self.__driver = webdriver.Chrome(executable_path='chromedrive-handle', options=self.__options)
        self.__wait = WebDriverWait(self.__driver, 10)  # 由于加载页面是需要时间等待故引入时间等待；
        self.__login_url = 'https://login.taobao.com/member/login.jhtml'
        self.__index_url = 'https://www.taobao.com/'

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
            #   重新跳转到主页
            self.__redirect(url=self.__index_url)
            return True
        except Exception as e:
            logging.ERROR('登录出错:',e.__str__())
            logging.exception("Exception occurred")
            return False

    def __search(self):
        #   检索产品
        input =self.__get_element_located(By.CSS_SELECTOR, '#q')
        # 模拟了一个提交按钮查询对应的信息（注意在这里可以灵活使用不同的选择器有时候报错就是选择的选择器问题导致）
        submit = self.__get_element_clickable(By.XPATH, '//*[@id="J_TSearchForm"]/div[1]/button')
        # 模拟输入内容后、再提交信息
        input.send_keys(self.product)
        submit.click()

    def __get_product_info(self):
        #   该方法用于解析当前网页的数据
        html = self.__driver.page_source  # 获取整个网页的源代码
        doc = pq(html)
        items = doc('#mainsrp-itemlist .items .item').items()  # 获取所有循环的内容
        for item in items:
            print(item)
            # product = {
            #     'image': item.find('.pic .img').attr('src'),
            #     'price': item.find('.price').text(),
            #     'deal': item.find('.deal-cnt').text()[0:-3],
            #     'title': item.find('.title').text().replace('\n', ''),
            #     'shop': item.find('.shop').text(),
            #     'location': item.find('.location').text()
            # }
            # print(product)

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
            self.__search()
            #   检查搜索结果页面是否加载完成
            self.__get_element_located(By.CSS_SELECTOR, '#mainsrp-itemlist .items .item')
            self.__get_product_info()
            # 获取返回的总页数
            totile = self.__get_element_located(By.XPATH, '//*[@id="mainsrp-pager"]/div/div/div/div[1]').text
            sum = int(re.search('(\d+)', totile, re.S).group(1))  # 打印出总页数
            for i in range(2, sum + 1):
                self.__next_page(i)
        else:
            #登录失败
            pass

    def release_resouce(self):
        self.__driver.close()

def main():
    username = ''   # 输入登录帐号
    pwd = ''    # 输入登录密码
    produce = '护肤品'     # 输入要搜索的产品名
    taobao = TaobaoSpider(username=username, password=pwd,product=produce)
    taobao.start()
    time.sleep(100)
    taobao.release_resouce()

if __name__ == '__main__':
    main()
