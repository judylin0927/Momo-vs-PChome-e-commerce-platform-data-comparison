import pymysql
import jieba
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from datetime import datetime
import os

# 資料庫連接設定
db_config = {
    'host': '',  # 資料庫主機
    'port': ,
    'user': '',  # 資料庫用戶名
    'password': '',  # 資料庫密碼
    'database': ''  # 資料庫名稱
}

# 停用詞列表（可以根據需要擴充）
STOP_WORDS = set([
    "我", " " ,"https", "www", "但是", "大家", "PChome", "jpeg", "pchome", "這個", "那個",
    "kobo", "tw", "momoshop", "MoMo", "MOMO", "http", "第一", "就是", "家裡", "Momoji",
    "png", "然後是", "Momo", "com", "momo", "jpg", "cc", "reurl", "因為", "所以", "一下",
    "1", "bit", "連結", "imgur", "你", "的", "了", "是", "在", "有", "和", "就", "不",
    "也", "這", "他", "她", "它", "我們", "他們", "她們", "買", "PCHOME", "一個", "看到",
    "顯示", "可以", "要", "收到", "後", "到", "但", "跟", "來", "知道", "還是", "直接", "真的", "如果", "沒有"
])

# 手動加載字體文件
font_path = os.path.expanduser("~/.fonts/NotoSansCJK-Regular.ttc")
custom_font = FontProperties(fname=font_path)

# 連接資料庫並讀取資料，按照momo pchome做過濾
def read_from_db(keyword=None):
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    # 若提供了關鍵字，則過濾資料
    if keyword:
        query = f"SELECT `article_content` FROM articles WHERE `keyword` = '{keyword}'"
    else:
        query = "SELECT `article_content` FROM articles"
    
    cursor.execute(query)
    data = [row['article_content'] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return data

# 提取上下文
def extract_contexts(contents, keyword="有人", window=3):
    contexts = []
    
    for content in contents:
        words = jieba.lcut(content)  # 分詞
        if keyword in words:
            index = words.index(keyword)
            # 抓取前後的詞作為上下文
            start = max(0, index - window)
            end = min(len(words), index + window + 1)
            context = words[start:end]
            contexts.append(" ".join(context))
    
    return contexts

# 找出和 "有人" 常搭配的詞
def get_top_word_combinations(contexts):
    word_combinations = Counter()
    
    for context in contexts:
        words = jieba.lcut(context)
        for word in words:
            if word not in STOP_WORDS and len(word) > 1:  # 過濾停用詞
                word_combinations[word] += 1
    
    return word_combinations.most_common(50)

# 生成並保存詞雲圖像
def generate_wordcloud(top_words, keyword="有人"):
    wordcloud = WordCloud(font_path=font_path, width=800, height=400).generate_from_frequencies(dict(top_words))
    
    # 生成動態檔案名稱，附加時間戳
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'/home/judy/one_stop/picture/{keyword}_{timestamp}.png' 
    
    # 保存為圖片文件
    plt.figure(figsize=(10, 6))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")
    plt.savefig(filename)  # 保存圖片
    plt.close()  # 關閉圖形，釋放資源
    
    return filename  # 返回保存的檔案路徑

# 主函數
def main():
    # 分別處理 PChome 和 momo 平台的資料
    pchome_data = read_from_db("PChome")  # 讀取 PChome 平台的文章
    momo_data = read_from_db("momo")  # 讀取 momo 平台的文章
    
    # 提取包含「有人」的上下文
    pchome_contexts = extract_contexts(pchome_data)
    momo_contexts = extract_contexts(momo_data)
    
    # 找出常見搭配詞
    pchome_top_words = get_top_word_combinations(pchome_contexts)
    momo_top_words = get_top_word_combinations(momo_contexts)
    
    # 生成並保存 PChome 的詞雲圖像
    pchome_image_path = generate_wordcloud(pchome_top_words, keyword="PChome")
    print(f"PChome 詞雲圖已保存為：{pchome_image_path}")
    
    # 生成並保存 momo 的詞雲圖像
    momo_image_path = generate_wordcloud(momo_top_words, keyword="momo")
    print(f"Momo 詞雲圖已保存為：{momo_image_path}")

if __name__ == "__main__":
    main()
