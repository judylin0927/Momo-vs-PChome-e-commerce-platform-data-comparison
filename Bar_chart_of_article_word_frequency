import pymysql  # 使用 pymysql 進行資料庫連接
from collections import Counter
import jieba
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from datetime import datetime  # 引入 datetime 模組來生成時間戳
import os

# 手動加載字體文件 ( 若無sudo權限下載，可下載該字體文件做引用，使圖片能正常產出中文字)
font_path = os.path.expanduser("~/.fonts/NotoSansCJK-Regular.ttc")
custom_font = FontProperties(fname=font_path)

# 停用詞列表（可以根據需要擴充）
STOP_WORDS = set([
    "我", " " ,"https", "www", "但是", "大家", "PChome", "jpeg", "pchome", "這個", "那個",
    "kobo", "tw", "momoshop", "MoMo", "MOMO", "http", "第一", "就是", "家裡", "Momoji",
    "png", "然後是", "Momo", "com", "momo", "jpg", "cc", "reurl", "因為", "所以", "一下",
    "1", "bit", "連結", "imgur", "你", "的", "了", "是", "在", "有", "和", "就", "不",
    "也", "這", "他", "她", "它", "我們", "他們", "她們", "買","PCHOME","一個","看到","顯示","今天","發現",
    "可以", "要", "收到", "後", "到", "但", "跟", "來","知道","還是","直接","真的","如果","沒有"
])

# 資料庫連接設定
db_config = {
    'host': '',  # 資料庫主機
    'port': ,
    'user': '',       # 資料庫用戶名
    'password': '',  # 資料庫密碼
    'database': ''   # 資料庫名稱
}

# 連接資料庫並讀取資料
def read_from_db():
    # 建立資料庫連線
    conn = pymysql.connect(**db_config)  # 使用 pymysql 連接
    cursor = conn.cursor(pymysql.cursors.DictCursor)  # 使用 DictCursor 來支持字典型結果

    # 查詢資料（表格名稱為 articles，若有異動table名稱，此處也需要更動）
    query = "SELECT keyword, `article_title`, `article_content` FROM articles"
    cursor.execute(query)

    data = {}

    # 讀取查詢結果並分類
    for row in cursor.fetchall():
        keyword = row['keyword']
        title = row['article_title']
        article_content = row['article_content']

        if keyword not in data:
            data[keyword] = {'titles': [], 'contents': []}

        data[keyword]['titles'].append(title)
        data[keyword]['contents'].append(article_content)

    # 關閉連接
    cursor.close()
    conn.close()

    return data

# 分詞並統計詞頻 (top_n=5 可以調整，目前為前五大常出現的詞彙)
def get_top_words(contents, keyword, top_n=5):
    words = []

    # 只處理內文(原先只處理標題，但字數太少不宜以此為判斷)
    for content in contents:
        seg_list = jieba.lcut(content)
        # 使用 set 來去除同一篇文章中重複的詞彙
        filtered_words = set([
            word for word in seg_list
            if word not in STOP_WORDS and len(word) > 1 and word.isalpha()  # 保留至少兩個字的有效中文
        ])
        words.extend(filtered_words)

    # 統計詞頻
    word_count = Counter(words)
    # 返回前 top_n 個常見詞
    return word_count.most_common(top_n)


# 生成直條圖並保存為文件
def plot_bar_chart(word_counts, keyword):
    words, counts = zip(*word_counts)
    plt.figure(figsize=(10, 6))
    bars = plt.bar(words, counts, color='skyblue')
    plt.xlabel('詞語', fontproperties=custom_font)
    plt.ylabel('出現次數', fontproperties=custom_font)
    plt.title(f'關鍵字 "{keyword}" 的常見詞頻', fontproperties=custom_font)
    plt.xticks(rotation=45, fontproperties=custom_font)
    plt.tight_layout()  # 避免標籤被截斷

    # 在每個條形上方顯示對應的數字
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval + 0.05,  # 文字位置
                 str(int(yval)), ha='center', va='bottom', fontproperties=custom_font)

    # 生成動態檔案名稱，附加時間戳
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'/home/{keyword}_bar_chart_{timestamp}.png' # 要儲存的PNG檔案的路徑及檔名

    plt.savefig(filename)  # 保存為圖片文件
    plt.close()  # 關閉圖形，釋放資源

# 主函數
def main():
    data = read_from_db()  # 從資料庫讀取資料

    for keyword, articles in data.items():
        print(f"關鍵字: {keyword}")
        contents = articles['contents']

        top_words = get_top_words(contents, keyword)
        for word, count in top_words:
            print(f"{word}: {count} 次")
        print("-" * 40)

        # 生成直條圖
        plot_bar_chart(top_words, keyword)

if __name__ == "__main__":
    main()
