import pymysql
import matplotlib.pyplot as plt
from datetime import datetime

# ====== 資料庫連線設定 ======
db_config = {
    'host': '',
    'port': ,
    'user': '',
    'password': '',
    'database': ''
}

# ========== 從資料庫讀取分數 ==========
def read_data_from_db():
    """
    從 DB 讀取 keyword 和 sentiment_score，
    並分別存入 pchome_scores、momo_scores。
    """
    pchome_scores = []
    momo_scores = []

    try:
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # 假設我們只需要抓有 sentiment_score 的資料
        query = "SELECT keyword, sentiment_score FROM articles WHERE sentiment_score IS NOT NULL"
        cursor.execute(query)
        rows = cursor.fetchall()

        for row in rows:
            keyword = row['keyword']
            score = float(row['sentiment_score'])

            # 根據關鍵字分類
            if keyword == 'PChome':
                pchome_scores.append(score)
            elif keyword == 'momo':
                momo_scores.append(score)

        cursor.close()
        conn.close()

    except pymysql.MySQLError as e:
        print(f"資料庫錯誤: {e}")

    return pchome_scores, momo_scores

# ========== 計算情感分數區間的數量 ==========
def calculate_score_ranges(scores):
    """
    將情感分數分為 5 個區間，回傳每個區間的計數。
    """
    ranges = {
        '0-20': 0,
        '21-40': 0,
        '41-60': 0,
        '61-80': 0,
        '81-100': 0
    }

    for score in scores:
        if 0 <= score <= 20:
            ranges['0-20'] += 1
        elif 21 <= score <= 40:
            ranges['21-40'] += 1
        elif 41 <= score <= 60:
            ranges['41-60'] += 1
        elif 61 <= score <= 80:
            ranges['61-80'] += 1
        elif 81 <= score <= 100:
            ranges['81-100'] += 1

    return ranges

# ========== 畫出圓餅圖 ==========
def plot_pie_chart(pchome_ranges, momo_ranges):
    labels = ['0-20', '21-40', '41-60', '61-80', '81-100']
    pchome_data = [pchome_ranges[label] for label in labels]
    momo_data = [momo_ranges[label] for label in labels]

    # 建立子圖
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))

    # ---------------- PChome 圖 ----------------
    wedges1, texts1, autotexts1 = ax1.pie(
        pchome_data, 
        labels=labels,          # 若想在圖上也顯示標籤，可保留
        autopct='%1.1f%%', 
        startangle=90, 
        colors=['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#c2c2f0'],
        pctdistance=0.85,        # 調整百分比位置(往中心移)
        labeldistance=1.05,     # 調整標籤與中心距離(越大越往外)
        wedgeprops={'width': 0.4, 'edgecolor': 'white'},  # << 設定甜甜圈厚度
        textprops={'fontsize': 10}
    )
    ax1.set_title('PChome Sentiment Score Distribution', fontsize=12)
    ax1.axis('equal')  # 讓圓餅圖保持正圓

    # ---------------- momo 圖 ----------------
    wedges2, texts2, autotexts2 = ax2.pie(
        momo_data, 
        labels=labels,
        autopct='%1.1f%%',
        startangle=90, 
        colors=['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#c2c2f0'],
        pctdistance=0.85,
        labeldistance=1.05,
        wedgeprops={'width': 0.4, 'edgecolor': 'white'},
        textprops={'fontsize': 10}
    )
    ax2.set_title('momo Sentiment Score Distribution', fontsize=12)
    ax2.axis('equal')

    # 儲存圖檔
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'/home/sentiment_analysis_pie_chart_{timestamp}.png'

    plt.tight_layout()  # 自動調整子圖間距
    plt.savefig(filename)
    print(f"圖像已儲存為 {filename}")

# ========== 主程式 ==========
def main():
    pchome_scores, momo_scores = read_data_from_db()

    # 如果都沒有資料，可以提示或結束
    if not pchome_scores and not momo_scores:
        print("無法取得任何 PChome 或 momo 的分數資料，請檢查資料庫。")
        return

    pchome_ranges = calculate_score_ranges(pchome_scores)
    momo_ranges = calculate_score_ranges(momo_scores)

    plot_pie_chart(pchome_ranges, momo_ranges)

if __name__ == "__main__":
    main()

