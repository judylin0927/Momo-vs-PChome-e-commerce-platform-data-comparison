import pymysql
import pandas as pd
from collections import Counter
import matplotlib.pyplot as plt
import datetime

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
    conn = pymysql.connect(**db_config, cursorclass=pymysql.cursors.DictCursor)  # 使用 DictCursor
    cursor = conn.cursor()

    # 查詢資料（假設表格名稱為 articles）
    query = "SELECT article_title, article_content, article_date, keyword FROM articles"
    cursor.execute(query)

    # 讀取資料並轉換為 pandas DataFrame
    rows = cursor.fetchall()
    df = pd.DataFrame(rows)

    # 關閉連接
    cursor.close()
    conn.close()

    return df

# 從資料庫讀取資料
df = read_from_db()

# 檢查 Article Date 欄位的日期格式是否正確
print(df['article_date'].head())  # 檢查幾個日期

# 確保 Article Date 轉換為日期格式
df['article_date'] = pd.to_datetime(df['article_date'], errors='coerce')

# 去除多餘空格並將 Keyword 統一為大寫
df['keyword'] = df['keyword'].str.strip().str.upper()

# 提取季度
df['quarter'] = df['article_date'].dt.to_period('Q')  # 提取季度（例如：2025Q1）

# 選擇將 NaT 的行排除掉
df = df.dropna(subset=['article_date'])

# 初始化按季度統計
pchome_quarter_counts = Counter()  # PCHOME 的季度統計
momo_quarter_counts = Counter()    # MOMO 的季度統計

# 遍歷每篇文章並分析
for index, row in df.iterrows():
    article_content = row['article_content']
    keyword = row['keyword']  # 獲取 Keyword 欄位
    quarter = row['quarter']  # 獲取季度欄位
    
    # 檢查文章是否有內容
    if pd.notna(article_content):
        # 如果文章關鍵詞是 PCHOME 或 MOMO
        if keyword == "PCHOME":
            pchome_quarter_counts[quarter] += 1
        elif keyword == "MOMO":
            momo_quarter_counts[quarter] += 1

# 輸出按季度統計的 PCHOME 次數
print("PCHOME 每個季度出現的次數：")
for quarter, count in pchome_quarter_counts.items():
    print(f"{quarter}: {count}")

print("\n")

# 輸出按季度統計的 MOMO 次數
print("MOMO 每個季度出現的次數：")
for quarter, count in momo_quarter_counts.items():
    print(f"{quarter}: {count}")

# 繪製折線圖
quarters = sorted(set(pchome_quarter_counts.keys()).union(momo_quarter_counts.keys()))

# 將季度轉換為字符串格式
quarters_str = [str(qtr) for qtr in quarters]

pchome_counts = [pchome_quarter_counts.get(qtr, 0) for qtr in quarters]
momo_counts = [momo_quarter_counts.get(qtr, 0) for qtr in quarters]

plt.figure(figsize=(10, 6))
plt.plot(quarters_str, pchome_counts, label='PCHOME', marker='o', color='blue')
plt.plot(quarters_str, momo_counts, label='MOMO', marker='o', color='red')

# 在每個數據點上顯示數字，調整數字位置
for i, txt in enumerate(pchome_counts):
    plt.text(quarters_str[i], pchome_counts[i] + 0.1, str(txt), color='blue', ha='center', va='bottom', fontsize=10)

for i, txt in enumerate(momo_counts):
    plt.text(quarters_str[i], momo_counts[i] + 0.1, str(txt), color='red', ha='center', va='bottom', fontsize=10)

# 標題和標籤
plt.title('PCHOME vs MOMO in Different Quarters', fontsize=14)
plt.xlabel('Quarter', fontsize=12)
plt.ylabel('Number of Articles', fontsize=12)

# 顯示圖例
plt.legend()

# 顯示圖形
plt.xticks(rotation=45)  # 旋轉季度標籤以便清晰顯示
plt.tight_layout()  # 調整佈局以避免標籤重疊

# 生成動態檔案名稱，附加當前時間戳
timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
file_name = f'/home/Quarter_Stats_{timestamp}.png'

# 儲存圖像
plt.savefig(file_name)

# 顯示成功訊息
print(f"圖像已成功儲存為: {file_name}")

# 顯示圖形
plt.show()
