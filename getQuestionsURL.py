import os
import time
import urllib.parse
import subprocess

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from login import login_in

def getCurrentPageQuestions(browser, already_exist_urls, answered_urls, answered_file):
    # 寻找所有的问题帖子，并搜集问题的href链接
    answereds = browser.find_elements_by_css_selector('#SearchMain div[class="Card SearchResult-Card"] .AnswerItem')
    for each in answereds:
        divEle = each
        metaEle = divEle.find_element_by_css_selector('meta[itemprop*="url"]')
        href = metaEle and metaEle.get_attribute('content')
        # 可能没有找到对应的元素，就直接过滤
        # 需要判断这个url是否已经存在当前的txt中
        if (href and (href not in already_exist_urls)):
            answered_urls.append(href)
            already_exist_urls.append(href)
            print("get answered question url: ", href)

            # 获取到一个新的url写入到文本
            write2txt(href, answered_file)


def crawlKeywordsHierarchy(browser, keywords, already_exist_urls, answered_file):
    print("In crawlKeywordsHierarchy() keywords: ", keywords, "...")

    # Starting node link
    # 根据关键词搜索相关的帖子
    url = 'https://www.zhihu.com/search?q=' + urllib.parse.quote(keywords) + '&type=content&vertical=answer'

    browser.get(url)

    # 存储有回答和没回答的帖子
    answered_urls = []

    # 循环下滑，收集对应关键词的所有相关问题
    # 每次向下滚动500px
    src = ""
    src_updated = browser.page_source
    same_page_count = 0
    while True:
        # 记录之前的页面信息
        src = src_updated
        # 滚动500px
        browser.execute_script("window.scrollBy(0, 500);")
        browser.implicitly_wait(5)
        # 获取页面滚动后的信息
        src_updated = browser.page_source

        # 判断滚动是否会导致页面内容变化（加载新的数据）
        # 累计如果滚动100次都没有加载新的数据，就向上滚动（可能存在页面卡住的情况）
        if (src == src_updated):
            same_page_count += 1
        if (same_page_count > 100):
            same_page_count = 0
            browser.execute_script("window.scrollBy(0, -50);")
            browser.implicitly_wait(5)
            src_updated = browser.page_source

        # 每次页面滚动之后，都进行解析页面，获取当前页面的问题url
        getCurrentPageQuestions(browser, already_exist_urls, answered_urls, answered_file)

        try:
            # 寻找问题加载完成时的“没有更多了”按钮，结束滚动加载（表明没有相关问题了）
            more_button = browser.find_element_by_class_name('css-7hmi9v')
            if more_button.text == '没有更多了':
                print("normal break")
                break
        except Exception as e:
            # print(e)
            continue
        continue

    return answered_urls

def write2txt(url, file):
    file.write(url+"\n")
    file.flush()
    print("write ", url, " to file ")

def readTxt(file, already_exist_urls):
    file.seek(0)
    lines = file.readlines()
    if (len(lines)):
        for line in lines:
            already_exist_urls.append(line.strip())

def getQuestionsUrlsByKeywords(keywords):
    # 先调用cmd命令创建一个自己打开的浏览器
    # subprocess.run('C:/Program Files/Google/Chrome/Application/chrome.exe --remote-debugging-port=9222 --user-data-dir="D:/Crawler_NLP_Analysis/myself_zhihu/selenium_data"')

    chromedriver = "chromedriver"
    os.environ["webdriver.chrome.driver"] = chromedriver
    # 用selenium接管这个浏览器
    chrome_options = Options()
    # # 禁用sandbox，让Chrome在root权限下跑
    # chrome_options.add_argument('--no-sandbox')
    # chrome_options.add_argument('--disable-dev-shm-usage')
    # 根据调用cmd命令创建的浏览器设置的端口号来填写
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    browser = webdriver.Chrome(chrome_options=chrome_options)

    # 用于记录问题的文本
    answered_file_path = '.\\'+keywords+'_AnsweredQuestionUrls.txt'
    # txt中已经存在的urls
    already_exist_urls = []

    # 记录问题的txt文本存在则直接读取内容，不存在则会创建
    answered_file = open(answered_file_path, 'a+')

    # 读取已经收集到的问题url
    readTxt(answered_file, already_exist_urls)

    # 账号登录（因为知乎要登录）
    login_in(browser)

    # 关键词搜索，获取问题帖子
    # 这里返回的answered_urls是每次程序运行后追加到txt中的新url，暂时没有用处
    answered_urls = crawlKeywordsHierarchy(browser, keywords, already_exist_urls, answered_file)

    answered_file.close()

    # 这里不能用quit关闭，因为这个浏览器是我们通过cmd创建的，关闭后就没了

if __name__ == "__main__":
    keywordsList = ['中国 碳中和']
    # 问题收集
    for keyword in keywordsList:
        print("search keyword ", keyword)
        print("start get keyword-related questions")
        getQuestionsUrlsByKeywords(keyword)
        time.sleep(5)
