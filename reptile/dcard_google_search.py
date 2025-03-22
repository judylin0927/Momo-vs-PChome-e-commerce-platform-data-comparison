import os
import re
import logging
import httpx
import pandas as pd
import mysql.connector
from typing import List, Dict, Any
from datetime import datetime, timedelta, date
import calendar

# --------------------- Logging 設定 ---------------------
log_dir = './log'  # 設定 log 存放目錄
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, 'dcard_google_search.log')  # 設定 log 檔案名稱
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file),  # 將 log 寫入檔案
        logging.StreamHandler()  # 同時輸出到 console
    ]
)

class GoogleCustomSearch:
    def __init__(self, api_key: str, search_engine_id: str, db_config: Dict):
        """初始化 Google Custom Search 客戶端。
        
        Args:
            api_key (str): Google Custom Search API 的 API Key
            search_engine_id (str): Google Custom Search Engine 的 ID
            db_config (Dict): 資料庫連接配置
        """
        self.api_key = api_key
        self.search_engine_id = search_engine_id
        self.base_url = 'https://www.googleapis.com/customsearch/v1'  # Google Custom Search API 的基礎 URL
        self.db_config = db_config

    def _clean_title(self, title: str) -> str:
        """清理文章標題，移除不必要的後綴（如「網路購物板」或「Dcard」）。
        
        Args:
            title (str): 原始標題
            
        Returns:
            str: 清理後的標題
        """
        parts = re.split(r'\s*-\s*', title)
        if len(parts) > 1:
            suffix = parts[-1].strip()
            # 如果後綴以「網路購物板」或「網路購物版」或「Dcard」開頭，就移除
            if re.match(r"^(網路購物(?:板|版)?|Dcard)", suffix, re.IGNORECASE):
                return " - ".join(parts[:-1]).strip()
        return title.strip()

    def _clean_content(self, snippet: str) -> str:
        """清理文章內容，移除時間戳和省略號。
        
        Args:
            snippet (str): 原始內容
            
        Returns:
            str: 清理後的內容
        """
        # 移除標準格式日期
        date_pattern = r'^[A-Za-z]{3}\s+\d{1,2},\s+\d{4}\s+\.\.\.\s+'
        content = re.sub(date_pattern, '', snippet)
    
        # 移除 "X days ago"
        days_ago_pattern = r'^\d+\s+days?\s+ago\s+\.\.\.\s+'
        content = re.sub(days_ago_pattern, '', content)
    
        # 移除 "今天HH:MM"
        today_pattern = r'^Today\d{1,2}:\d{2}\s+\.\.\.\s+'
        content = re.sub(today_pattern, '', content)
    
        if content.rstrip().endswith('...'):
            content = content.rstrip()[:-3].rstrip()
        
        return content

    def _parse_date_from_snippet(self, snippet: str) -> datetime:
        """從文章內容中解析日期。
        
        支援的日期格式：
        - 標準格式：'Feb 5, 2025'
        - 幾天前：'4 days ago'
        - 今天時間：'今天17:35'
        
        Args:
            snippet (str): 文章內容
            
        Returns:
            datetime: 解析後的日期，若無法解析則返回 None
        """
        # 檢查標準格式 (Feb 5, 2025)
        standard_pattern = r'([A-Za-z]{3}\s+\d{1,2},\s+\d{4})'
        match = re.search(standard_pattern, snippet)
        if match:
            try:
                return datetime.strptime(match.group(1), '%b %d, %Y')
            except ValueError:
                logging.warning(f"無法解析標準日期格式: {match.group(1)}")
                return None
            
        # 檢查 "X days ago" 格式
        days_ago_pattern = r'(\d+)\s+days?\s+ago'
        match = re.search(days_ago_pattern, snippet)
        if match:
            try:
                days = int(match.group(1))
                return datetime.now() - timedelta(days=days)
            except ValueError:
                logging.warning(f"無法解析 'days ago' 格式: {match.group(1)}")
                return None
            
        # 檢查 "今天HH:MM" 格式
        today_pattern = r'今天(\d{1,2}):(\d{2})'
        match = re.search(today_pattern, snippet)
        if match:
            try:
                hour = int(match.group(1))
                minute = int(match.group(2))
                today = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
                return today
            except ValueError:
                logging.warning(f"無法解析 '今天' 格式: {match.group(0)}")
                return None
            
        logging.info(f"在內容中未找到可識別的日期格式: {snippet[:100]}...")
        return None

    def update_search_progress(self, platform: str, start_date: datetime, end_date: datetime) -> None:
        """更新搜尋進度。
        
        Args:
            platform (str): 平台名稱
            start_date (datetime): 搜尋開始日期
            end_date (datetime): 搜尋結束日期
        """
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE wilson_search_progress 
                SET last_search_start = %s, 
                    last_search_end = %s
                WHERE platform = %s
            """, (start_date.date(), end_date.date(), platform))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logging.info(f"更新 {platform} 的搜尋進度: {start_date.date()} 到 {end_date.date()}")
            
        except Exception as e:
            logging.error(f"更新搜尋進度時發生錯誤: {e}")

    def _get_search_period(self, platform) -> tuple[datetime, datetime]:
        """確定搜尋的時間區間。
        
        首先檢查搜尋進度表，如果沒有則從2020年12月31日開始搜尋。
        無論是否找到符合的結果，都會更新搜尋進度。
        
        Returns:
            tuple[datetime, datetime]: (開始日期, 結束日期)
        """
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            # 檢查搜尋進度表
            cursor.execute("""
                SELECT last_search_end 
                FROM wilson_search_progress
                WHERE platform = %s;
            """, (platform,))
            
            result = cursor.fetchone()
            
            current_date = datetime.now()
            
            if not result:
                # 如果沒有進度記錄，從2020年12月31日開始
                start_date = datetime(2020, 12, 31)
                
                # 計算結束日期（起始日期後的第三個月的第一天）
                month = start_date.month + 3
                year = start_date.year
                if month > 12:
                    year += month // 12
                    month = month % 12
                    if month == 0:
                        month = 12
                        year -= 1
                end_date = datetime(year, month, 1)
                
                # 插入初始進度記錄
                cursor.execute("""
                    INSERT INTO wilson_search_progress (platform, last_search_start, last_search_end)
                    VALUES (%s, %s, %s)
                """, (platform, start_date.date(), end_date.date()))
                
            else:
                # 從上次搜尋的結束日期開始
                last_end_date = result[0]
                if isinstance(last_end_date, date):
                    last_end_date = datetime.combine(last_end_date, datetime.min.time())
                
                start_date = last_end_date
                
                # 計算新的結束日期（起始日期後的第三個月的第一天）
                month = start_date.month + 3
                year = start_date.year
                if month > 12:
                    year += month // 12
                    month = month % 12
                    if month == 0:
                        month = 12
                        year -= 1
                end_date = datetime(year, month, 1)
                
                # 如果結束日期超過當前時間，調整搜尋區間
                if end_date > current_date:
                    if current_date.month == 1:
                        start_date = datetime(current_date.year - 1, 12, 31)
                    else:
                        last_month = current_date.month - 1
                        last_day = calendar.monthrange(current_date.year, last_month)[1]
                        start_date = datetime(current_date.year, last_month, last_day)
                    
                    month = current_date.month + 3
                    year = current_date.year
                    if month > 12:
                        year += month // 12
                        month = month % 12
                        if month == 0:
                            month = 12
                            year -= 1
                    end_date = datetime(year, month, 1)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return start_date, end_date

        except Exception as e:
            logging.error(f"在 _get_search_period 中發生錯誤: {e}")
            return datetime(2020, 12, 31), datetime(2021, 3, 1)
        
    def _get_search_start_date(self, platform: str) -> datetime:
        """根據資料庫中的最新文章日期，計算搜尋的開始日期。
        
        Args:
            platform (str): 平台名稱 ('PChome' 或 'Momo')
            
        Returns:
            datetime: 搜尋開始日期
        """
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT MAX(publish_date) 
                FROM wilson_search_results 
                WHERE platform = %s
            """, (platform,))
            
            latest_date = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            if latest_date:
                # 從最新日期減去一天，確保不會漏掉任何文章
                return latest_date - timedelta(days=1)
            else:
                return datetime(2020, 12, 31)
            
        except Exception as e:
            logging.error(f"在 _get_search_start_date 中發生資料庫錯誤: {e}")
            return datetime(2020, 12, 31)

    def _url_exists(self, article_url: str) -> bool:
        """檢查 URL 是否已經存在於資料庫中。
        
        Args:
            article_url (str): 要檢查的文章 URL
            
        Returns:
            bool: 如果 URL 存在則返回 True，否則返回 False
        """
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM wilson_search_results WHERE article_url = %s;", (article_url,))
            count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            return count > 0
            
        except Exception as e:
            logging.error(f"檢查 URL 是否存在時發生資料庫錯誤: {e}")
            return False

    def search(self, platform: str) -> List[Dict[Any, Any]]:
        """執行 Google Custom Search，並根據日期過濾結果。"""
        start_date, end_date = self._get_search_period(platform)
        
        query = platform.lower()
        date_query = (f"{query} "
                    f"after:{start_date.strftime('%Y-%m-%d')} "
                    f"before:{end_date.strftime('%Y-%m-%d')}")
        
        logging.info(f"搜尋 {platform} 文章，時間範圍: "
                    f"{start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}")
        
        search_results = []
        start_index = 1
        
        while len(search_results) < 100:
            response = self._make_request(date_query, start=start_index)
            items = response.get('items', [])
            if not items:
                break
                
            for item in items:
                article_title = item.get('title', '')
                article_url = item.get('link', '')
                if platform in article_title.lower() and self._url_exists(article_url):
                    continue
                    
                publish_date = self._parse_date_from_snippet(item.get('snippet', ''))
                if publish_date:
                    if isinstance(publish_date, date):
                        publish_date = datetime.combine(publish_date, datetime.min.time())
                    if start_date <= publish_date < end_date:
                        processed_result = {
                            'title': self._clean_title(item.get('title', '')),
                            'article_url': article_url,
                            'content': self._clean_content(item.get('snippet', '')),
                            'platform': platform,
                            'publish_date': publish_date
                        }
                        search_results.append(processed_result)
                
            start_index += 10
            if start_index > 100:
                break
        
        # 無論是否找到結果，都更新搜尋進度
        self.update_search_progress(platform, start_date, end_date)
        
        # 根據日期排序結果（降序）
        search_results.sort(key=lambda x: x['publish_date'], reverse=True)
        
        return search_results

    def _make_request(self, query: str, **params) -> Dict:
        """向 Google Custom Search API 發送請求。
        
        Args:
            query (str): 搜尋查詢
            **params: 其他搜尋參數
            
        Returns:
            Dict: API 返回的 JSON 數據
        """
        params = {
            'key': self.api_key,
            'cx': self.search_engine_id,
            'q': query,
            **params
        }
        
        response = httpx.get(self.base_url, params=params)
        response.raise_for_status()
        return response.json()

    def initialize_database(self) -> None:
        """初始化資料庫，創建必要的表格。"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            # 創建搜尋結果表格
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS wilson_search_results (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    platform ENUM('PChome', 'Momo') NOT NULL,
                    title TEXT NOT NULL,
                    article_url TEXT NOT NULL,
                    content TEXT NOT NULL,
                    publish_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY article_url_idx (article_url(255))
                )
            """)
            
            # 創建搜尋進度追蹤表格
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS wilson_search_progress (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    platform VARCHAR(50) NOT NULL,
                    last_search_start DATE NOT NULL,
                    last_search_end DATE NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY platform_idx (platform)
                )
            """)
            
            conn.commit()
            cursor.close()
            conn.close()
            logging.info("資料庫初始化成功。")
            
        except Exception as e:
            logging.error(f"資料庫初始化錯誤: {e}")

    def save_to_database(self, results: List[Dict]) -> None:
        """將搜尋結果保存到 MySQL 資料庫。
        
        Args:
            results (List[Dict]): 處理後的搜尋結果
        """
        # 先過濾結果
        filtered_results = [
            result for result in results 
            if result['platform'].lower() in result['title'].lower()
        ]
        
        if not filtered_results:
            logging.info(f"沒有包含平台關鍵字的結果需要保存到資料庫")
            return
            
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            for result in filtered_results:
                try:
                    cursor.execute("""
                        INSERT INTO wilson_search_results 
                        (platform, title, article_url, content, publish_date)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        result['platform'],
                        result['title'],
                        result['article_url'],
                        result['content'],
                        result['publish_date']
                    ))
                except mysql.connector.IntegrityError as e:
                    if e.errno == 1062:  # 重複條目錯誤
                        continue  # 跳過此記錄
                    raise
            
            conn.commit()
            cursor.close()
            conn.close()
            logging.info(f"數據成功保存到資料庫。總記錄數: {len(filtered_results)}")
            
        except Exception as e:
            logging.error(f"保存到資料庫時發生錯誤: {e}")
        
    def save_to_csv(self, results: List[Dict], platform: str) -> None:
        """將搜尋結果保存到 CSV 文件。

        Args:
            results (List[Dict]): 處理後的搜尋結果
            platform (str): 平台名稱 ('PChome' 或 'Momo')
        """
        if not results:
            logging.info(f"沒有結果需要保存到 CSV 文件: {platform}")
            return
            
        # 篩選出標題包含平台關鍵字的結果
        filtered_results = [
            result for result in results 
            if platform.lower() in result['title'].lower()
        ]
        
        if not filtered_results:
            logging.info(f"沒有包含 {platform} 的結果需要保存到 CSV")
            return
            
        try:
            # 處理日期格式
            for result in filtered_results:
                if result['publish_date']:
                    result['publish_date'] = result['publish_date'].strftime('%Y-%m-%d')
                    
            df = pd.DataFrame(filtered_results)

            # 指定 CSV 存放的資料夾
            csv_dir = os.path.join("..", "scrape_results")
            if not os.path.exists(csv_dir):
                os.makedirs(csv_dir)
            
            # 為每個平台創建獨立的 CSV 檔案
            filename = os.path.join(csv_dir, f"{platform.lower()}_search_results.csv")

            # 如果檔案存在且不為空，則讀取並合併新資料
            if os.path.exists(filename) and os.path.getsize(filename) > 0:
                try:
                    existing_df = pd.read_csv(filename)
                    df = pd.concat([existing_df, df]).drop_duplicates(subset=['article_url'])
                except pd.errors.EmptyDataError:
                    logging.warning(f"現有的 CSV 文件 {filename} 為空或損壞。創建新文件。")
            
            # 保存到 CSV
            df.to_csv(filename, index=False)
            logging.info(f"CSV 文件保存到 {filename}，總記錄數: {len(df)}")
            
        except Exception as e:
            logging.error(f"保存到 CSV 時發生錯誤: {str(e)}")

def main():
    # 設定 API Key 和 Search Engine ID
    api_key = '???'  # 替換為你的 Google Custom Search API Key
    search_engine_id = '???'  # 替換為你的 Google Custom Search Engine ID
    
    # 資料庫配置
    db_config = {
        'host': '???',  # 資料庫主機
        'user': '???',  # 資料庫用戶名
        'port': ???,     # 資料庫端口
        'password': '???',  # 資料庫密碼
        'database': '???'  # 資料庫名稱
    }
    
    # 初始化搜尋客戶端
    search_client = GoogleCustomSearch(api_key, search_engine_id, db_config)
    
    # 初始化資料庫
    search_client.initialize_database()
    
    try:
        platforms = ['PChome', 'Momo']
        
        for platform in platforms:
            # 獲取搜尋結果
            results = search_client.search(platform)
            
            if results:
                # 保存到資料庫
                search_client.save_to_database(results)
                
                # 保存到 CSV
                search_client.save_to_csv(results, platform)
                
                logging.info(f"{platform} 的搜尋完成")
                logging.info(f"找到的新結果總數: {len(results)}")
            else:
                logging.info(f"沒有找到 {platform} 的新結果")
            
    except httpx.HTTPError as e:
        logging.error(f"API 錯誤: {e}")
    except Exception as e:
        logging.error(f"發生未預期的錯誤: {e}")

if __name__ == '__main__':
    main()
