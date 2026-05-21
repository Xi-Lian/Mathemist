"""
检测CSV文件的编码
"""

import chardet

if __name__ == "__main__":
    path = 'd:\\Git_Repository\\Mathemist\\learning_resource\\概率与统计-教案资源信息汇总表.csv'
    with open(path, 'rb') as f:
        data = f.read()
        result = chardet.detect(data)
        print(result)
