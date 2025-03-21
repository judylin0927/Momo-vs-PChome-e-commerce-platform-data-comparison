import pymysql
import requests
import bs4
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv
import os
from datetime import datetime
import re

# 設定 Chrome 選項（無頭模式）
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")  # 啟用無頭模式
chrome_options.add_argument("--disable-gpu")  # 在某些系統上需禁用 GPU 加速
chrome_options.add_argument("--no-sandbox")  # 針對 Linux 系統提高穩定性
chrome_options.add_argument("--disable-dev-shm-usage")  # 避免資源問題
chrome_options.add_argument("--window-size=1920,1080")  # 模擬正常視窗大小

# 自動安裝和管理 WebDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# 關鍵字列表 (可以自行增加關鍵字 於PTT - 網購版 搜尋該詞彙的文章內容)
keywords = ["PChome", "momo"]

# MariaDB 連接設定
db_config = {
    'host': '',  # 資料庫主機
    'port': ,
    'user': '',       # 資料庫用戶名
    'password': '',  # 資料庫密碼
    'database': ''   # 資料庫名稱
}

# 連接到 MariaDB 使用 PyMySQL
try:
    conn = pymysql.connect(**db_config)  # 使用 pymysql.connect()
    cursor = conn.cursor()
    print("成功連接到 MariaDB")
except pymysql.MySQLError as e:  # 捕捉 pymysql 的錯誤
    print(f"連接到 MariaDB 失敗: {e}")
    exit()

# 建立資料表（如果不存在） 
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INT AUTO_INCREMENT PRIMARY KEY,
            keyword VARCHAR(255),
            article_title TEXT,
            article_date VARCHAR(255),
            article_content TEXT,
            sentiment_score DECIMAL(5, 2) DEFAULT NULL,  # 情感分數欄位
            UNIQUE (keyword, article_title)  # 確保 (keyword, article_title) 組合唯一
        )
    """)
    print("資料表已建立或已存在")
except pymysql.MySQLError as e:  # 捕捉 pymysql 的錯誤
    print(f"建立資料表失敗: {e}")
    exit()

# 設定爬蟲下來後 CSV 存檔的完整路徑
csv_dir = '/home/csv'
csv_file = os.path.join(csv_dir, 'articles.csv') # 檔案名稱  (所以該檔案的位置為/home/csv/articles.csv)

# 如果目錄不存在，則創建它
if not os.path.exists(csv_dir):
    os.makedirs(csv_dir)

# 刪除原來的 CSV 檔案（如果存在；僅保留最新爬蟲的csv資訊）
if os.path.exists(csv_file):
    os.remove(csv_file)

# 初始化 CSV 檔案（若不存在則新增標題行）
try:
    with open(csv_file, mode='x', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Keyword", "Article Title", "Article Date", "Article Content", "Sentiment Score"])
except FileExistsError:
    pass

# 解析文章內容的函數
def parse_article_content(url):
    my_headers = {'cookie': 'over18=1;'}
    response = requests.get(url, headers=my_headers)
    soup = bs4.BeautifulSoup(response.text, "html.parser")

    header = soup.find_all('span', 'article-meta-value')
    if len(header) >= 4:
        # meta 一般順序：作者、看板、標題、日期
        title = header[2].text.strip()
        date_str = header[3].text.strip()
        
        # 用 PTT 常見格式解析日期
        try:
            date_obj = datetime.strptime(date_str, "%a %b %d %H:%M:%S %Y")
            formatted_date = date_obj.strftime("%Y-%m-%d")
        except ValueError:
            formatted_date = "無日期"
    else:
        title = "無標題"
        formatted_date = "無日期"

    main_container = soup.find(id='main-container')
    if main_container:
        all_text = main_container.text
        pre_text = all_text.split('--')[0]
        texts = pre_text.split('\n')
        contents = texts[2:]
        content = '\n'.join(contents)
        if '※ 發信站' in content:
            content = content.split('※ 發信站')[0]  # 如果在文章當中出現※ 發信站就停止爬取，改換下一個文章內容繼續爬取
    else:
        content = "無內容"

    return title, formatted_date, content

try:
    driver.get("https://www.ptt.cc/bbs/e-shopping/index.html") # 若不想爬取網購版，可以改這裡的網址!
    wait = WebDriverWait(driver, 10)

    for keyword in keywords:
        search_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input.query[name="q"]')))
        search_box.clear()
        time.sleep(1)
        search_box.send_keys(keyword)
        search_box.send_keys(Keys.RETURN)
        print(f"正在搜尋關鍵字: {keyword}")
        time.sleep(3)

        stop_processing = False
        page = 1
        while True:
            if stop_processing:
                break

            print(f"正在抓取關鍵字: {keyword} 的第 {page} 頁內容") # 可以看出目前爬取到哪一個關鍵詞的第幾頁面 !
            articles = driver.find_elements(By.CSS_SELECTOR, '.r-ent')

            if articles:
                for article in articles:
                    try:
                        title_element = article.find_element(By.CSS_SELECTOR, '.title')
                        title = title_element.text.strip()

                        try:
                            title_link = title_element.find_element(By.TAG_NAME, 'a')
                            article_url = title_link.get_attribute('href')

                            article_title, article_date, article_content = parse_article_content(article_url)

                            # 如果同時抓不到標題與日期，直接跳過
                            if article_title == "無標題" and article_date == "無日期":
                                print(">>> 同時無標題＆無日期，跳過該文章。")
                                continue

                            # 如果發現 2020 年就停止該關鍵字 (僅搜尋最新的到2021年的文章)
                            if "2020" in article_date:
                                print(f"發現 2020 年的文章，停止處理關鍵字: {keyword}")
                                stop_processing = True
                                break

                            # Debug 印出
                            print(f"文章標題: {article_title}")
                            print(f"文章日期: {article_date}")
                            print(f"文章內容: {article_content}")
                            print("-" * 50)

                            # 寫入資料庫
                            try:
                                cursor.execute(
                                    "SELECT id FROM articles WHERE keyword = %s AND article_title = %s",
                                    (keyword, article_title)
                                )
                                if cursor.fetchone() is None:
                                    cursor.execute(
                                        """
                                        INSERT INTO articles 
                                            (keyword, article_title, article_date, article_content, sentiment_score)
                                        VALUES (%s, %s, %s, %s, NULL)
                                        """,
                                        (keyword, article_title, article_date, article_content)
                                    )
                                    conn.commit()
                                    print(f"已存入 MariaDB: {article_title}")
                                else:
                                    print(f"資料已存在，不再寫入：關鍵字 '{keyword}', 標題 '{article_title}'")
                            except pymysql.MySQLError as e:
                                print(f"資料庫操作失敗: {e}")

                            # 寫入 CSV
                            with open(csv_file, mode='a', newline='', encoding='utf-8') as file:
                                writer = csv.writer(file)
                                writer.writerow([keyword, article_title, article_date, article_content, None])
                                print(f"已存入 CSV: {article_title}")

                        except Exception as e:
                            print(f"無法進入文章頁面: {e}")
                    except Exception as e:
                        print(f"無法處理文章: {e}")
            else:
                print(f"關鍵字: {keyword} 的第 {page} 頁沒有找到文章")

            # 點擊上一頁按鈕翻頁 ( 觀察 開發者F12 Elements 當中class的按鍵，模擬使用者按下上一頁)
            try:
                prev_page_button = driver.find_element(By.XPATH, '//a[@class="btn wide" and contains(text(), "上頁")]')
                prev_page_button.click()
                time.sleep(3)
                page += 1
            except Exception as e:
                print(f"無法點擊上一頁按鈕: {e}")
                break

finally:
    cursor.close()
    conn.close()
    print("MariaDB 連接已關閉")
    driver.quit()

