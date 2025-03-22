import mysql.connector
import logging
import pandas as pd
from datetime import datetime
from openai import OpenAI

# 設定 OpenAI API
api_key = 'sk-p???'

client = OpenAI(api_key=api_key)

# MySQL 資料庫設定
db_config = {
    'host': '',
    'user': '',
    'password': '',
    'database': ''
}

# 設定 LOG
log_file = "./log/filtered_news.log"
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logging.info("===== 啟動 filtered_news.py =====")

def get_latest_urls():
    """取得 filtered_news 中最新的 PChome 和 Momo 文章 URL（各平台各一筆）"""
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT t.platform, t.article_url
        FROM wilson_filtered_news t
        INNER JOIN (
            SELECT platform, MAX(publish_date) AS max_date
            FROM wilson_filtered_news
            WHERE platform IN ('PChome', 'Momo')
            GROUP BY platform
        ) m ON t.platform = m.platform AND t.publish_date = m.max_date;
    """
    cursor.execute(query)
    latest_urls = {row['platform']: row['article_url'] for row in cursor.fetchall()}

    cursor.close()
    conn.close()
    
    logging.info(f"找到最新的 URL: {latest_urls}")
    return latest_urls


def get_latest_ids(latest_urls):
    """根據最新的 article_url 找到 PChome 和 Momo News 中的對應 ID"""
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    latest_ids = {}

    for platform, table in [('PChome', 'wilson_pchome_news'), ('Momo', 'wilson_momo_news')]:
        if platform in latest_urls:
            query = f"SELECT id FROM {table} WHERE article_url = %s"
            cursor.execute(query, (latest_urls[platform],))
            result = cursor.fetchone()
            if result:
                latest_ids[platform] = result['id']

    cursor.close()
    conn.close()
    
    logging.info(f"找到最新的 ID: {latest_ids}")
    return latest_ids

def get_new_articles(latest_ids):
    """從最新的 ID 之後獲取新文章"""
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    new_articles = []

    for platform, table in [('PChome', 'wilson_pchome_news'), ('Momo', 'wilson_momo_news')]:
        last_id = latest_ids.get(platform, 0)  # 若沒有找到 ID，則從 ID 0 開始
        query = f"""
            SELECT id, title, article_url, content, publish_date 
            FROM {table} 
            WHERE id > %s 
            AND article_url NOT IN (SELECT article_url FROM wilson_filtered_news)
            ORDER BY id ASC
        """

        cursor.execute(query, (last_id,))
        articles = [{**row, "platform": platform} for row in cursor.fetchall()]
        new_articles.extend(articles)

    cursor.close()
    conn.close()
    
    logging.info(f"找到 {len(new_articles)} 篇新文章需處理")
    return new_articles

def extract_promo_info(text, publish_date):
    """使用 OpenAI API 提取行銷活動摘要"""
    prompt = f"這段發布於{publish_date}的新聞內容是否包含行銷活動（如折扣、促銷、滿額贈、會員優惠）？如果有，請用一句話摘要活動內容，否則回應'無活動'。\n\n{text}"

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            store=True,
            messages=[{"role": "user", "content": prompt}]
        )
        summary = completion.choices[0].message.content
        return summary if "無活動" not in summary else None
    except Exception as e:
        logging.error(f"OpenAI API 呼叫失敗: {e}")
        return None

def save_to_filtered_news(new_articles):
    """將處理後的文章存入 filtered_news 並寫入 CSV"""
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    inserted_articles = []

    for article in new_articles:
        # 先檢查是否已存在相同的 article_url 且 summary 不為 NULL
        cursor.execute("SELECT summary FROM wilson_filtered_news WHERE article_url = %s", (article['article_url'],))
        existing_summary = cursor.fetchone()
        
        if existing_summary and existing_summary[0] is not None:
            logging.info(f"跳過文章: {article['article_url']}，已有 summary")
            continue  # 若 summary 已存在則跳過處理

        # 呼叫 OpenAI API 獲取摘要
        summary = extract_promo_info(article['content'], article['publish_date'])
        if summary:
            article['summary'] = summary  
            query = """
                INSERT INTO wilson_filtered_news (platform, title, publish_date, article_url, summary, content)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE summary=VALUES(summary), content=VALUES(content)
            """
            cursor.execute(query, (
                article['platform'],
                article['title'],
                article['publish_date'],
                article['article_url'],
                summary,
                article['content']
            ))
            inserted_articles.append(article)

    conn.commit()
    cursor.close()
    conn.close()

    logging.info(f"已儲存 {len(inserted_articles)} 篇文章到 filtered_news")
    
    if inserted_articles:
        df = pd.DataFrame(inserted_articles)
        df.to_csv("../scrape_results/filtered_news.csv", index=False)
        logging.info("已更新 filtered_news.csv")

def main():
    logging.info("開始處理新文章")
    
    try:
        latest_urls = get_latest_urls()
        latest_ids = get_latest_ids(latest_urls)
        new_articles = get_new_articles(latest_ids)

        if new_articles:
            save_to_filtered_news(new_articles)
            logging.info(f"完成處理，共更新 {len(new_articles)} 篇文章")
        else:
            logging.info("沒有新文章需要處理")
    except Exception as e:
        logging.error(f"執行過程發生錯誤: {e}")

if __name__ == "__main__":
    main()
    logging.info("===== filtered_news.py 執行完畢 =====")
