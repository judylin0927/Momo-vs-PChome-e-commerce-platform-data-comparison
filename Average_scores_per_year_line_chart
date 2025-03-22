import pymysql
import matplotlib.pyplot as plt
from collections import defaultdict
from datetime import datetime

# ======= 資料庫連線設定 =======
db_config = {
    'host': '',
    'port': ,
    'user': '',
    'password': '',
    'database': ''
}

# 讀取資料庫資料並根據年份進行分組
def read_data_from_db():
    pchome_scores_by_year = defaultdict(list)
    momo_scores_by_year = defaultdict(list)

    try:
        # 連接資料庫
        connection = pymysql.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database'],
            cursorclass=pymysql.cursors.DictCursor
        )

        with connection.cursor() as cursor:
            table_name = "articles"

            # 查詢資料
            query = f"""
                SELECT keyword, sentiment_score, article_date
                FROM {table_name}
                WHERE article_date IS NOT NULL AND sentiment_score IS NOT NULL
            """
            cursor.execute(query)
            rows = cursor.fetchall()

            for row in rows:
                keyword = row['keyword']
                sentiment_score = float(row['sentiment_score'])
                article_date = row['article_date']

                # 確保日期有效
                if not article_date:
                    continue

                try:
                    # 取得文章的年份
                    year = article_date.year  # 如果 article_date 是 datetime 格式
                except AttributeError:
                    try:
                        year = datetime.strptime(article_date, '%Y-%m-%d').year
                    except ValueError:
                        continue

                # 根據 keyword 分組資料
                if keyword.lower() == "pchome":
                    pchome_scores_by_year[year].append(sentiment_score)
                elif keyword.lower() == "momo":
                    momo_scores_by_year[year].append(sentiment_score)

    except pymysql.MySQLError as e:
        print("資料庫連線或查詢時發生錯誤:", e)
    finally:
        if 'connection' in locals():
            connection.close()

    return pchome_scores_by_year, momo_scores_by_year

# 計算每年平均的情感分數
def calculate_average_sentiment(scores_by_year):
    avg_scores_by_year = {}
    for year, scores in scores_by_year.items():
        avg_scores_by_year[year] = sum(scores) / len(scores)
    return avg_scores_by_year

# 畫出情感分析隨時間變化的折線圖
def plot_line_chart(pchome_avg_scores, momo_avg_scores):
    plt.figure(figsize=(10, 6))  # 設定圖形大小

    # 繪製 PChome 和 momo 的折線圖
    plt.plot(list(pchome_avg_scores.keys()), list(pchome_avg_scores.values()), label='PChome', color='blue', marker='o')
    plt.plot(list(momo_avg_scores.keys()), list(momo_avg_scores.values()), label='momo', color='red', marker='o')

    # 設定標題與標籤
    plt.title('Sentiment Analysis of PChome and momo Over Time')
    plt.xlabel('Year')
    plt.ylabel('Average Sentiment Score')

    # 顯示圖例
    plt.legend()

    # 生成動態檔案名稱，附加時間戳
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'/home/sentiment_analysis_time_series_{timestamp}.png'  # 使用時間戳生成檔案名

    # 儲存圖像
    plt.savefig(filename)
    print(f"折線圖已儲存為 {filename}")  # 顯示成功訊息

# 主程式執行流程
def main():
    # 從資料庫讀取資料
    pchome_scores_by_year, momo_scores_by_year = read_data_from_db()

    # 計算每年平均情感分數
    pchome_avg_scores = calculate_average_sentiment(pchome_scores_by_year)
    momo_avg_scores = calculate_average_sentiment(momo_scores_by_year)

    # 繪製折線圖
    plot_line_chart(pchome_avg_scores, momo_avg_scores)

# 執行主程式
if __name__ == "__main__":
    main()
