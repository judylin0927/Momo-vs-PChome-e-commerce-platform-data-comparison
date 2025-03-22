import pymysql
import matplotlib.pyplot as plt
from datetime import datetime

# =========== 資料庫連線設定 ============
db_config = {
    'host': '',
    'port': ,
    'user': '',
    'password': '',
    'database': ''
}

# 讀取資料庫中的 date, score, keyword
def read_data_from_db():
    article_dates = []
    sentiment_scores = []
    keywords = []

    try:
        # 連接資料庫
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # 假設資料表名稱為 articles，且有 article_date, sentiment_score, keyword 欄位
        query = "SELECT id, article_date, sentiment_score, keyword FROM articles"
        cursor.execute(query)
        rows = cursor.fetchall()

        for row in rows:
            # 取得文章日期欄位
            date_str = row['article_date']
            if not date_str:  # 如果日期是空的，跳過
                continue

            # 將日期字串解析為 datetime 物件
            try:
                # 假設你的 article_date 是 "YYYY-MM-DD" 格式，若不同需調整
                article_date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                print(f"警告: 無效的日期格式，跳過該筆資料 - ID: {row['id']}")
                continue

            # 取得情感分數 (若為 None 或空值，也可自行判斷是否跳過)
            score = row.get('sentiment_score', None)
            if score is None:
                continue

            # keyword
            keyword = row.get('keyword', '未知')

            # 加入到列表
            article_dates.append(article_date)
            sentiment_scores.append(float(score))
            keywords.append(keyword)

        cursor.close()
        conn.close()

    except pymysql.MySQLError as e:
        print(f"資料庫錯誤: {e}")

    return article_dates, sentiment_scores, keywords

# 繪製散佈圖
def plot_scatter(article_dates, sentiment_scores, keywords):
    plt.figure(figsize=(10, 6))  # 設定圖形大小

    # 手動指定顏色
    color_map = {
        'momo': 'red',    # momo 使用紅色
        'PChome': 'blue',  # PChome 使用藍色
    }
    default_color = 'green'  # 其他關鍵字使用預設綠色

    # 根據關鍵字分配顏色並繪製散佈圖
    # 這裡先取 set(keywords) 獲得所有關鍵字的獨立列表，然後分批畫散點
    for keyword in set(keywords):
        # 找出該關鍵字所在索引
        keyword_indices = [i for i, kw in enumerate(keywords) if kw == keyword]

        # 根據索引取對應日期與分數
        k_dates = [article_dates[i] for i in keyword_indices]
        k_scores = [sentiment_scores[i] for i in keyword_indices]

        # 查詢 color_map 是否有定義顏色，否則用 default_color
        color = color_map.get(keyword, default_color)

        plt.scatter(k_dates, k_scores, label=keyword, color=color)

    # 設定標題與標籤
    plt.title('Sentiment Analysis of Articles')
    plt.xlabel('Year')
    plt.ylabel('Sentiment Score')

    # 格式化 x 軸為年份
    plt.gca().xaxis.set_major_locator(plt.matplotlib.dates.YearLocator())  # 每年一格
    plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y'))  # 只顯示年份
    plt.gcf().autofmt_xdate()  # 自動旋轉日期標籤

    # 顯示圖例
    plt.legend(loc='upper left')

    # 動態檔名
    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'/home/sentiment_analysis_by_year_{now_str}.png'

    # 儲存圖像並顯示
    plt.tight_layout()
    plt.savefig(filename)
    print(f"圖像已儲存為 {filename}")

# 主程式
def main():
    article_dates, sentiment_scores, keywords = read_data_from_db()
    if not article_dates:
        print("無法取得任何有效的日期與分數資料，請檢查資料庫內容。")
        return
    plot_scatter(article_dates, sentiment_scores, keywords)

if __name__ == "__main__":
    main()



