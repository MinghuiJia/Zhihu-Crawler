import time

from getQuestionsURL import getQuestionsUrlsByKeywords
from getAnswers import getAnsweredInfo

if __name__ == "__main__":
    keywordsList = ['中国 碳中和']
    # 问题收集
    for keyword in keywordsList:
        print("search keyword ", keyword)
        print("start get keyword-related questions")
        getQuestionsUrlsByKeywords(keyword)
        time.sleep(5)

        # 回答获取
        getAnsweredInfo('.\\'+keyword+'_AnsweredQuestionUrls.txt')

