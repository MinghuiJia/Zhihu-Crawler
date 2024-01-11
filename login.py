import os
import random
import time

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC  # 等待条件类
from selenium.webdriver.common.action_chains import ActionChains  # 动作类
from selenium.webdriver.chrome.options import Options

import cv2
from urllib import request

def save_cookie(browser):
    cookie = {}
    for item in browser.get_cookies():
        cookie[item['name']] = item['value']
    print(cookie)
    print("成功获取登录知乎后的cookie信息")

# 封装的计算图片距离的算法
def get_pos(imageSrc, templateSrc):
    # 对背景图片进行滤波处理和边缘提取
    image = cv2.imread(imageSrc)
    # GaussianBlur方法进行图像模糊化/降噪操作
    # 它基于高斯函数（也称为正态分布）创建一个卷积核（或称为滤波器），该卷积核应用于图像上的每个像素点。
    imageBlurred = cv2.GaussianBlur(image, (5, 5), 0, 0)
    # Canny方法进行图像边缘检测
    # image: 输入的单通道灰度图像。
    # threshold1: 第一个阈值，用于边缘链接。一般设置为较小的值。
    # threshold2: 第二个阈值，用于边缘链接和强边缘的筛选。一般设置为较大的值
    imageCanny = cv2.Canny(imageBlurred, 0, 100)  # 轮廓

    # 对滑块图片进行滤波处理和边缘提取
    template = cv2.imread(templateSrc)
    templateBlurred = cv2.GaussianBlur(template, (5, 5), 0, 0)
    templateCanny = cv2.Canny(templateBlurred, 0, 100)  # 轮廓

    # 模板匹配
    result = cv2.matchTemplate(imageCanny, templateCanny, cv2.TM_CCOEFF_NORMED)

    # 找到最大值和最大值的位置
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    # 找到匹配位置的左上角和右下角坐标
    w, h = template.shape[:2]
    top_left = max_loc
    bottom_right = (top_left[0] + w, top_left[1] + h)

    # 在大图上标记匹配位置
    cv2.rectangle(image, top_left, bottom_right, (0, 0, 255), 2)

    # # 显示结果
    # cv2.imshow('result', image)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    cv2.imwrite("bigImageWithPositionArea.png", image)
    return top_left

# 滑块验证
def slide_verify(browser):
    # 获取登录按钮并点击
    submitButtonEle = browser.find_element_by_class_name('SignFlow-submitButton')
    submitButtonEle.click()

    time.sleep(3)
    # 使用浏览器隐式等待3秒
    # browser.implicitly_wait(3)

    # 等待滑块验证图片加载后，再做后面的操作
    WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, 'yidun-custom')))

    # 获取背景图网址
    bgImgEle = browser.find_element_by_class_name('yidun_bg-img')
    bgImgSrc = bgImgEle.get_attribute('src')
    # 获取滑块图网址
    templateImgEle = browser.find_element_by_class_name('yidun_jigsaw')
    templateImgSrc = templateImgEle.get_attribute('src')

    # 下载上述两个图片至本地
    request.urlretrieve(bgImgSrc, 'bigImage.png')
    request.urlretrieve(templateImgSrc, 'templateImage.png')

    # 等待图片下载好
    time.sleep(5)

    # 计算缺口图像的x轴位置（横向位置）
    dis = get_pos('bigImage.png', 'templateImage.png')
    # 实际距离要向右平移10px（根据实际情况）
    dis = dis[0] + 10

    # 获取小滑块元素
    sliderEle = browser.find_element_by_class_name('yidun_slider')
    time.sleep(3)

    # 按下小滑块并不松开
    ActionChains(browser).click_and_hold(sliderEle).perform()
    time.sleep(3)

    # 移动小滑块，模拟人的操作，一次次移动一点点
    i = 0
    moved = 0
    while moved < dis:
        x = random.randint(3, 10)  # 每次移动3到10像素
        moved += x
        ActionChains(browser).move_by_offset(xoffset=x, yoffset=0).perform()
        print("第{}次移动后，位置为{}".format(i, sliderEle.location['x']))
        i += 1

    # 移动完之后，松开鼠标
    ActionChains(browser).release().perform()
    time.sleep(3)

    # 登录成功的判断，根据是否有class为AppHeader-profile的元素
    try:
        element = browser.find_element_by_class_name('AppHeader-profile')
    except:
        return False
    else:
        return True

# 登录
def login_in(browser):
    # 账号密码
    username = '18163539190'
    password = 'JMHjmh1998'
    loginUrl = 'https://www.zhihu.com/signin?next=%2F'
    browser.get(loginUrl)

    try:
        if (browser.find_element_by_class_name('AppHeader-profile')):
            print("已经登录成功了")
            save_cookie(browser)
    except:
        # 切换到登录页面
        passwordLoginEle = browser.find_elements(By.CLASS_NAME, 'SignFlow-tab')[1]
        passwordLoginEle.click()
        time.sleep(3)

        # 获取账号密码输入框元素，并填写内容
        usernameEle = browser.find_element_by_name('username')
        passwordEle = browser.find_element_by_name('password')
        usernameEle.send_keys(username)
        passwordEle.send_keys(password)
        time.sleep(1)

        if (slide_verify(browser)):
            print("登录成功")
            save_cookie(browser)
        else:
            print('第1次登录失败')
            for i in range(4):
                print('正在尝试第%d次登录'%(i+2))
                if (slide_verify(browser)):
                    print('第%d次登录成功'%(i+2))
                    save_cookie(browser)
                    browser.close()
                    return
                print('第%d次登录失败'%(i+2))
            print('登录失败5次，停止登录')

if __name__ == "__main__":
    chromedriver = "chromedriver"
    os.environ["webdriver.chrome.driver"] = chromedriver
    # 用selenium接管这个浏览器
    chrome_options = Options()
    # # 禁用sandbox，让Chrome在root权限下跑
    # chrome_options.add_argument('--no-sandbox')
    # chrome_options.add_argument('--disable-dev-shm-usage')
    # 根据调用cmd命令创建的浏览器设置的端口号来填写
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")  # 前面设置的端口号
    browser = webdriver.Chrome(chrome_options=chrome_options)  # executable执行webdriver驱动的文件

    # 账号登录
    login_in(browser)
