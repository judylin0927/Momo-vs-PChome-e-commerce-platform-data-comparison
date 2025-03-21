import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict
from datetime import datetime
import pymysql

# ======= 資料庫連線設定 =======
db_config = {
    'host': '',
    'port': ,
    'user': '',
    'password': '',
    'database': ''
}

def main():
    # 1. 連接資料庫並以 Pandas 讀取資料
    try:
        conn = pymysql.connect(**db_config)
        # 取出 columns: id, keyword, sentiment_score
        query = """
            SELECT id, keyword, sentiment_score
            FROM articles
            WHERE sentiment_score IS NOT NULL
        """
        df = pd.read_sql(query, conn)
        conn.close()
    except pymysql.MySQLError as e:
        print(f"資料庫錯誤: {e}")
        return

    # 2. 定義分數區間
    bins = [0, 20, 40, 60, 80, 100]
    labels = ['0-20', '21-40', '41-60', '61-80', '81-100']

    # 3. 將 sentiment_score 分到相應區間 (類似 cut)
    df['score_range'] = pd.cut(df['sentiment_score'], bins=bins, labels=labels, right=True)

    # 4. 依照 keyword 和 score_range 分組，儲存對應的 id
    keyword_score_dict = {}

    for keyword in df['keyword'].unique():
        keyword_score_dict[keyword] = {}
        keyword_df = df[df['keyword'] == keyword]
        # 針對每個區間 label，取出對應 id
        for score_range in labels:
            ids_in_range = keyword_df[keyword_df['score_range'] == score_range]['id'].tolist()
            keyword_score_dict[keyword][score_range] = ids_in_range

    # 5. 幫每個區間的 id 添加換行處理：每行顯示 5 個 id
    def format_ids(ids):
        grouped_ids = [ids[i:i+5] for i in range(0, len(ids), 5)]
        # 每組用逗號分隔，再用換行分隔
        return "\n".join([", ".join(map(str, group)) for group in grouped_ids])

    # 6. 建立表格資料
    table_data = []
    for keyword in keyword_score_dict:
        row = [keyword]  # 行首顯示 keyword
        for score_range in labels:
            ids_str = format_ids(keyword_score_dict[keyword].get(score_range, []))
            row.append(ids_str)
        table_data.append(row)

    # 7. 表格欄位標題
    columns = ['Keyword'] + labels

    # 8. 使用 Matplotlib 顯示表格
    fig, ax = plt.subplots(figsize=(15, 10))  # 調整表格大小
    ax.axis('tight')
    ax.axis('off')

    table = ax.table(
        cellText=table_data,
        colLabels=columns,
        loc='center',
        cellLoc='center',
        rowLoc='center'
    )

    # 9. 調整表格樣式
    for (i, j), cell in table.get_celld().items():
        cell.set_text_props(fontsize=8)  # 調整一般單元格字體大小
        if i == 0:  # 表頭行
            cell.set_text_props(fontsize=10, weight='bold')
            cell.set_height(0.2)
        else:
            cell.set_edgecolor('black')
            cell.set_text_props(verticalalignment='center', horizontalalignment='center')
            cell.set_height(0.3)  # 增高以容納多行ID
            cell.set_width(0.15)  # 調整每欄寬度

    # 10. 動態檔名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'/home/score_table__{timestamp}.png'

    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"圖像已儲存為 {filename}")

if __name__ == "__main__":
    main()




