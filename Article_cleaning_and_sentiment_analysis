import pymysql
import re
import jieba
from openai import OpenAI 

# 手動設置金鑰；使用者需在此替換 API Key
client = OpenAI(api_key="sk-.....") 

# ====== 資料庫連線設定 ======
db_config = {
    'host': '',
    'port': ,
    'user': '',
    'password': '',
    'database': ''
}


# ====== 分析文章內容時，遇到以下 停用詞表 ，會自行刪除該詞，可自行增減 ====== 
STOP_WORDS = set([
    "的", "了", "是", "在", "我", "有", "這", "就", "也", "都", "嗎",
    "你", "說", "不", "和", "＊", "抱怨", "文", "一旦", "發文", "Y",
    "N", "/", "很", "可以", "可能"  
])


def clean_text(text):
    """
    先行文本清洗：移除網址、多餘標點等
    """
    # 去除 URL
    text = re.sub(r'http[s]?://\S+', '', text)

    # 只保留中英數字（其他符號一律變空白）
    text = re.sub(r'[^A-Za-z0-9\u4e00-\u9fa5]+', ' ', text)

    # 去除多餘空白
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    return text


def tokenize_and_filter(text):
    """
    使用 jieba 斷詞＋移除停用詞
    """
    words = jieba.lcut(text)
    filtered = [w for w in words if w not in STOP_WORDS]
    # 再次處理空白 (確保前面沒有空白)
    filtered_text = " ".join(filtered)
    filtered_text = re.sub(r'\s+', ' ', filtered_text).strip()
    return filtered_text


def sentiment_analysis(text):
    """
    呼叫 ChatGPT
    - 若超過 2000 字，做 chunk 分段
    - 對每段文本呼叫 GPT，要求只回傳「0~100」整數分數，最後取平均
    - 加入更詳盡的規則 + clamp(0~100) 處理
    """
    max_chunk_length = 2000
    if len(text) > max_chunk_length:
        chunks = [text[i : i + max_chunk_length] for i in range(0, len(text), max_chunk_length)]
    else:
        chunks = [text]

    total_score = 0
    for chunk in chunks:
        # 在 Prompt 中給出更具體規則
        prompt_content = (
            "請分析以下文本的情感，並給出 0 到 100 的整數分數（只輸出數字）。\n\n"
            "如果該文本看起來都是在生氣、抱怨、負面內容，請在 0～40 之間；"
            "若是大多負面但有一點客觀敘述，請在 41～50；若偏中立請在 51～60；"
            "若有小部分正面請在 61～70；正面佔多數請在 71～80；非常正面請在 81～90；"
            "極度正面請在 91～100。\n\n"
            "請不要多做任何解釋，只能回傳整數。若無法確定，請給大約 50。\n\n"
            f"以下是文本：{chunk}"
        )

        response = client.chat.completions.create(
            model="gpt-3.5-turbo", # 可依照需求調整模型
            messages=[
                {"role": "system", "content": "你是情感分析助手。"},
                {"role": "user", "content": prompt_content}
            ],
            temperature=0.0
        )

        # 解析 GPT 回應
        answer = response.choices[0].message.content.strip()
        # 只取數字部分
        score_str = re.sub(r'[^0-9]', '', answer)
        if score_str == "":
            print(f"無法解析分數：{answer}")
            return None

        try:
            score_int = int(score_str)
        except ValueError:
            print(f"無法轉成整數：{answer}")
            return None

        # ============== 做 clamp 保證分數介於 0～100 ==============
        if score_int < 0:
            score_int = 0
        elif score_int > 100:
            score_int = 100

        total_score += score_int

    # 若有分段，取平均
    final_score = total_score / len(chunks)
    return final_score


def main():
   """
    主函數：從 articles 表中讀取文章內容，並進行情感分析。
    1. 從資料庫中讀取以下欄位：
       - id: 文章的唯一識別碼
       - keyword: 文章的關鍵字
       - article_content: 文章的內容
       - article_date: 文章的日期
       - sentiment_score: 文章的情感分數（若為 NULL 表示尚未分析）
    2. 檢查 sentiment_score 是否已經有值：
       - 若已有值，則跳過該文章，避免重複分析（確保分數一致性，並節省資源）。
       - 若為 NULL，則進行文本清洗、分詞與情感分析，並將結果更新回資料庫。
    """
    try:
        # 連接到資料庫
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # 將 sentiment_score 一起撈出來，判斷是否為 None
        cursor.execute("""
            SELECT id, keyword, article_content, article_date, sentiment_score
            FROM articles
        """)
        rows = cursor.fetchall()

        for row in rows:
            article_id = row['id']
            keyword = row['keyword']
            article_date = row['article_date'] or ""
            raw_content = row['article_content'] or ""
            existing_score = row['sentiment_score']  # 可能是 None 或已經有數字

            # 如果已經有分數了，就跳過!避免出現每次執行AI判斷分數不同，保持已經爬取過的文章不被再次評分。
            if existing_score is not None:
                print(f"ID={article_id} 已經有 sentiment_score={existing_score}，跳過情感分析。")
                print("-" * 50)
                continue

            print(f"=== 處理 ID={article_id}, Keyword={keyword}, Date={article_date} ===")

            # 1) 清洗
            cleaned_text = clean_text(raw_content)
            # 2) 斷詞 & 過濾停用詞
            final_text = tokenize_and_filter(cleaned_text)

            # 3) 情感分析
            score = sentiment_analysis(final_text)
            if score is None:
                print("情感分析失敗，跳過。")
                continue

            print(f"分析結果分數: {score:.2f}")

            # 4) 更新 sentiment_score 欄位到 DB
            update_sql = """UPDATE articles SET sentiment_score = %s WHERE id = %s"""
            cursor.execute(update_sql, (score, article_id))
            conn.commit()

            print(f"已更新 ID={article_id} 的 sentiment_score。")
            print("-" * 50)

        cursor.close()
        conn.close()
        print("所有資料處理完成。")

    except pymysql.MySQLError as e:
        print(f"資料庫錯誤: {e}")
    except Exception as e:
        print(f"程式發生錯誤: {e}")


if __name__ == "__main__":
    main()
