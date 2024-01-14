import os
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from bs4 import BeautifulSoup

# import pymysql

def readTxt(file, already_exist_urls):
    file.seek(0)
    lines = file.readlines()
    if (len(lines)):
        for line in lines:
            already_exist_urls.append(line.strip())

def getFirstCommentButton(browser):
    time.sleep(3)
    # 获取页面所有card下的操作栏（点赞、评论等）
    allClickEles = browser.find_elements_by_css_selector('.ContentItem .RichContent .ContentItem-actions')
    # 获取页面所有的card
    allDivsEles = browser.find_elements_by_css_selector('.List-item')
    # 从每个操作栏中找到评论按钮，返回评论按钮及其对应的card元素
    for i in range(len(allDivsEles)):
        each = allClickEles[i]
        div = allDivsEles[i]
        buttons = each.find_elements_by_tag_name('button')
        commentButton = buttons[2]
        if (commentButton.text != '添加评论' and commentButton.text != "收起评论" and "评论" in commentButton.text):
            return commentButton, div
    return None, None

# def insertData2Mysql(sql, param):
#     # 存储到数据库
#     # 连接数据库
#     conn = pymysql.connect(host='localhost', port=3306,
#                            user='root', password='JMHjmh1998',
#                            database='crawlerdb')
#
#     # 使用 cursor() 方法创建一个游标对象 cursor
#     cursor = conn.cursor()
#
#     try:
#         cursor.execute(sql, param)
#         conn.commit()
#     except Exception as e:
#         print(e)
#         conn.rollback()
#     finally:
#         conn.close()

def getAnswerTimeAndIPInfo(href, ori_name, ori_time, browser):
    href = "https:"+href

    # 当前浏览器新打开一个tab访问题的回答
    # 记录原始窗口ID
    original_window = browser.current_window_handle
    # 在新的标签页打开链接
    browser.execute_script(f'window.open("{href}", "_blank");')
    time.sleep(3)
    # 切换到新的标签页
    browser.switch_to.window(browser.window_handles[-1])
    time.sleep(2)

    try:
        # 打开之后第一个回复应该就是查看的
        # 解析新的标签页的信息
        # 第一个回答的作者名字
        name = browser.find_element_by_css_selector('.AnswerCard .AuthorInfo meta[itemprop="name"]').get_attribute('content')
        # 第一个回答的时间元素
        answeredTimeEle = browser.find_element_by_css_selector('.RichContent .ContentItem-time')
        # 第一个回答的时间（不包含IP）
        answeredTimeText = answeredTimeEle.find_element_by_tag_name('span').get_attribute('aria-label')
        # 获取带有IP的时间字符串
        answeredTimeWithIP = answeredTimeEle.text

    except Exception as e:
        print(e)
        raise Exception('open profile page error or parse error...')
    finally:
        # 关闭当前标签tab页
        browser.close()
        time.sleep(2)
        # 切回到之前的标签页
        browser.switch_to.window(original_window)

    # 获取name和时间核实，一致再替换
    if (ori_name == name and ori_time == answeredTimeText):
        return answeredTimeWithIP

    return ""

def extractPageInfo(browser, url, keyword, func):
    # # 模拟点击评论的过程
    # while True:
    #     try:
    #         time.sleep(2)
    #         # 先获取第一个可以点击的按钮
    #         clickEle, divEle = getFirstCommentButton(browser)
    #         # 点击按钮，页面会更新
    #         if (clickEle):
    #             # 先让评论按钮在范围内，保证不会弹窗
    #             browser.execute_script("arguments[0].scrollIntoView(false)", divEle)
    #             time.sleep(1)
    #             clickEle2, divEle2 = getFirstCommentButton(browser)
    #             browser.execute_script("arguments[0].click();", clickEle2)
    #         # 当页面中没有评论需要点开就结束循环
    #         else:
    #             break
    #
    #         time.sleep(1.5)
    #     except (Exception, BaseException) as e:
    #         print(e)
    #         continue

    # 使用bs4解析页面信息
    html_source = browser.page_source
    soup = BeautifulSoup(html_source, 'html.parser')

    # 获取所有的回答card
    answereds = None
    try:
        # 寻找所有的回答
        answeredsDiv = soup.find('div', attrs={'id': 'QuestionAnswers-answers'})
        answereds = answeredsDiv.find_all('div', attrs={'class': 'List-item'})
    except Exception as e:
        print(e)
        time.sleep(300)

        # 如果出现任何意外就重新开始解析这个问题的帖子
        func(browser, url, keyword)

        return

    # 首先获取问题的名称和总回答数
    questionName = browser.find_element_by_css_selector('.QuestionHeader .QuestionHeader-title').text
    answerCount = browser.find_element_by_css_selector('.QuestionPage meta[itemprop="answerCount"]').get_attribute('content')
    print("collected ", len(answereds), " answer list-item")
    print("question name: ", questionName, " answer count: ", answerCount)

    # 解析每个回答
    upvoteCounts = []
    commentCounts = []
    contents = []
    profiles = []
    answerDateCreateds = []
    answeredTimeWithIPs = []

    # 记录解析到第几个回答
    processCount = 1
    for answered in answereds:
        try:
            print("processing answer ", processCount, ' start...')

            # 解析作者信息
            info1 = answered.find('div', attrs={'class': 'AuthorInfo'})
            # 作者名称
            name = info1.find('meta', attrs={'itemprop': 'name'})['content']
            # 作者个人信息链接
            profileHref = info1.find('meta', attrs={'itemprop': 'url'})['content']
            # 作者被关注人数
            followerCount = info1.find('meta', attrs={'itemprop': 'zhihu:followerCount'})['content']
            # 作者描述
            authorInfoDetail = info1.find('div', attrs={'class': 'AuthorInfo-detail'}).text

            # 帖子相关信息（赞同数量、回答创建时间、评论数量）
            upvoteCount = answered.find('meta', attrs={'itemprop': 'upvoteCount'})['content']
            dateCreated = answered.find('meta', attrs={'itemprop': 'dateCreated'})['content']
            commentCount = answered.find('meta', attrs={'itemprop': 'commentCount'})['content']

            # 获取帖子答案的文本内容
            content = answered.find('div', attrs={'class': 'RichContent'})
            text = content.find('div', attrs={'class': 'RichContent-inner'})
            temp_content = text.text

            # 获取帖子发布或编辑时间及a链接href，用于查看是否包含IP，包含就更新
            answeredTime = content.find('div', attrs={'class': 'ContentItem-time'})
            answeredTimeAHref = answeredTime.find('a')['href']
            answeredTimeText = answeredTime.find('span')['aria-label']

            # 更新带有IP的时间
            newAnsweredTimeText = getAnswerTimeAndIPInfo(answeredTimeAHref, name, answeredTimeText, browser)
            if (newAnsweredTimeText):
                answeredTimeText = newAnsweredTimeText

            # 所有信息解析完再对数据进行存储操作（防止某个解析崩掉信息不全，如果有信息没解析全，这条信息不会被记录）
            # 获取支持、评论数、作者基本信息
            upvoteCounts.append(upvoteCount)
            commentCounts.append(commentCount)
            profileList = [name, followerCount, authorInfoDetail]
            profiles.append(profileList)
            # 回答文本
            contents.append(temp_content)
            # 回答创建时间
            answerDateCreateds.append(dateCreated)
            # 回答发布或编辑时间（如有IP会带IP）
            answeredTimeWithIPs.append(answeredTimeText)

            # 数据预处理组织成存储到Mysql的形式
            param = (
                questionName,
                name,
                followerCount,
                authorInfoDetail,
                upvoteCount,
                dateCreated.split('T')[0],
                commentCount,
                temp_content,
                answeredTimeText,
                keyword
            )

            # # 数据存储到数据库
            # sql = '''
            #         INSERT INTO zhihu_answers(question_name,author_name,author_followers,author_describle,answer_upvotes,answer_create_time,answer_comment_count,answer_content,answer_post_time_ip,keyword) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            #           '''
            # insertData2Mysql(sql, param)

        except (Exception, BaseException) as e:
            print(e)
            continue
        finally:
            print("processing answer ", processCount, ' finished...')
            processCount += 1

    # 清除一下浏览器缓存
    # browser.delete_all_cookies()
    print(upvoteCounts)
    # print(contents)
    print("upvoteCounts length: ", len(upvoteCounts), " contents length: ", len(contents))

# 获取一个问题下的所有回答
def getNormalAnsweredInfo(browser, url, keyword):
    browser.get(url)

    # 下滑操作，直至所有的回答都搜集到
    src = ""
    src_updated = browser.page_source
    same_page_count = 0
    while True:
        # 执行滚动操作，每次滚动800px
        # 先保存滚动前的页面内容
        src = src_updated
        # 页面滚动
        browser.execute_script("window.scrollBy(0, 800);")
        browser.implicitly_wait(2)
        # 获取页面信息
        src_updated = browser.page_source
        # 判断滚动后页面信息是否更新
        if (src == src_updated):
            same_page_count += 1
        if (same_page_count > 100):
            same_page_count = 0
            browser.execute_script("window.scrollBy(0, -50);")
            browser.implicitly_wait(2)
            src_updated = browser.page_source
        try:
            # 寻找问题加载完成时的“写回答”按钮，结束滚动加载
            more_button = browser.find_element_by_class_name('QuestionAnswers-answerButton')
            if more_button.is_displayed():
                break
        except Exception as e:
            # print(e)
            continue
        continue

    extractPageInfo(browser, url, keyword, getNormalAnsweredInfo)

def getAnsweredInfo(answered_file_path):
    # chromedirver模拟操作浏览器
    chromedriver = "chromedriver"
    os.environ["webdriver.chrome.driver"] = chromedriver
    # 用selenium接管这个浏览器
    chrome_options = Options()
    # 禁止浏览器加载页面图片，防止问题答案过多，加载过程中导致内存不足
    chrome_options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")  # 前面设置的端口号
    browser = webdriver.Chrome(chrome_options=chrome_options)  # executable执行webdriver驱动的文件

    # 记录问题的txt文本存在则直接读取内容，不存在则会创建
    answered_file = open(answered_file_path, 'a+')

    # txt中已经存在的urls
    already_exist_urls = []
    # 读取已经收集到的问题url
    readTxt(answered_file, already_exist_urls)

    keyword = answered_file_path.split("\\")[-1].split("_")[0]

    for url in already_exist_urls:
        print(url, " question start crawler...")
        getNormalAnsweredInfo(browser, url, keyword)
        time.sleep(30)

    # browser.quit()

if __name__ == "__main__":
    keywordsList = ['中国 碳中和']
    # 问题收集
    for keyword in keywordsList:
        # 创建数据库
        getAnsweredInfo('.\\'+keyword+'_AnsweredQuestionUrls.txt')

