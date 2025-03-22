import os
import pymysql
import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from flask import Flask, request, jsonify, render_template_string, send_from_directory
from flask_restful import Api, Resource
from flasgger import Swagger
from flasgger.utils import swag_from
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import random
import datetime


##############################################
# 1. 建立 Flask 主應用
##############################################
app = Flask(__name__)
api = Api(app)

# Swagger 配置
app.config["SWAGGER"] = {
    "title": "MOMO 及 PChome 資料庫API",
    "version": "1.0",
    "description": "通過關鍵字查尋兩家電商資料庫的API",
    "uiversion": 3,  # 使用 Swagger UI 3
    "specs_route": "/swagger-ui/",  # 指定 Swagger UI 路由
}

# 初始化 Swagger
swagger = Swagger(app)

##############################################
# 2. 定義資料庫連接 & RESTful API
##############################################
db_config = {
    "host": "",  # 資料庫主機
    "port": ,
    "user": "",  # 資料庫用戶名
    "password": "",  # 資料庫密碼
    "database": "",  # 資料庫名稱
}
##############################################
# (A) 針對三張新 table 的「讀取」API (只提供 GET 查詢)
##############################################
class GetCSEOutcomes(Resource):
    def get(self):
        """
        取得資料庫中 Dcard 網購版的平台搜尋結果數據，可篩選特定時間範圍及指定回傳欄位
        Columns: [id,platform,publish_date,title,article_url,summary,content,created_at]
        ---
        parameters:
          - name: start_date
            in: query
            type: string
            required: false
            description: 起始日期 (YYYY-MM-DD)
          - name: end_date
            in: query
            type: string
            required: false
            description: 結束日期 (YYYY-MM-DD)
          - name: fields
            in: query
            type: string
            required: false
            description: 要回傳的欄位，格式 "col-1,col-2,col-3,..."
          - name: filters
            in: query
            type: string
            required: false
            description: 指定的欄位值過濾條件，格式 "col-1=val-1,col-n2=val-2,..."        
        responses:
          200:
            description: 返回指定時間範圍內及指定欄位的 Dcard 搜尋結果
        tags:
          - Dcard CSE Data
        """
        try:
            conn = pymysql.connect(**db_config)
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # 設定可選擇的欄位
            valid_fields = {"id", "platform", "title", "article_url", "content", "publish_date", "score"}
            selected_fields = "*"
            
            if 'fields' in request.args and request.args['fields']:
                user_fields = set(request.args['fields'].split(","))
                filtered_fields = valid_fields.intersection(user_fields)
                if filtered_fields:
                    selected_fields = ", ".join(filtered_fields)
                
            query = f"SELECT {selected_fields} FROM wilson_search_results WHERE 1=1"
            filters = []
            
            if 'start_date' in request.args and request.args['start_date']:
                query += " AND publish_date >= %s"
                filters.append(request.args['start_date'])
            
            if 'end_date' in request.args and request.args['end_date']:
                query += " AND publish_date <= %s"
                filters.append(request.args['end_date'])
            
            if 'filters' in request.args and request.args['filters']:
                filter_pairs = request.args['filters'].split(",")
                for pair in filter_pairs:
                    key, value = pair.split("=")
                    if key in valid_fields:
                        query += f" AND {key} = %s"
                        filters.append(value)
            
            query += " ORDER BY publish_date DESC"
            cursor.execute(query, tuple(filters))
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            return jsonify({"google_cse_results": results})
        except pymysql.MySQLError as e:
            return jsonify({"error": str(e)}), 500

class MomoMonthlyResource(Resource):
    def get(self):
        """
        讀 momo_monthly_revenue 表
        ---
        responses:
          200:
            description: momo_monthly_revenue 所有資料
        tags:
          - 歷史月度營收 (2021-2024)
        """
        try:
            conn = pymysql.connect(**db_config)
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT * FROM momo_monthly_revenue")
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return jsonify({"data": rows})
        except pymysql.MySQLError as e:
            return jsonify({"error": str(e)}), 500


class PchomeMonthlyResource(Resource):
    def get(self):
        """
        讀 pchome_monthly_revenue 表
        ---
        responses:
          200:
            description: pchome_monthly_revenue 所有資料
        tags:
          - 歷史月度營收 (2021-2024)
        """
        try:
            conn = pymysql.connect(**db_config)
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT * FROM pchome_monthly_revenue")
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return jsonify({"data": rows})
        except pymysql.MySQLError as e:
            return jsonify({"error": str(e)}), 500


class NewsResource(Resource):
    def get(self):
        """
        取得資料庫中 平台公告中心的活動訊息及摘要
        Columns: [id,platform,publish_date,title,article_url,summary,content,created_at]
        ---
        parameters:
          - name: start_date
            in: query
            type: string
            required: false
            description: 起始日期 (YYYY-MM-DD)
          - name: end_date
            in: query
            type: string
            required: false
            description: 結束日期 (YYYY-MM-DD)
          - name: fields
            in: query
            type: string
            required: false
            description: 要回傳的欄位，格式 "col-1,col-2,col-3,..."
          - name: filters
            in: query
            type: string
            required: false
            description: 指定的欄位值過濾條件，格式 "col-1=val-1,col-n2=val-2,..."        
        responses:
          200:
            description: 返回指定時間範圍內及指定欄位的 Dcard 搜尋結果
        tags:
          - 歷史公告
        """
        try:
            conn = pymysql.connect(**db_config)
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # 設定可選擇的欄位
            valid_fields = {"id", "platform", "title", "article_url", "content", "publish_date", "score"}
            selected_fields = "*"
            
            if 'fields' in request.args and request.args['fields']:
                user_fields = set(request.args['fields'].split(","))
                filtered_fields = valid_fields.intersection(user_fields)
                if filtered_fields:
                    selected_fields = ", ".join(filtered_fields)
                
            query = f"SELECT {selected_fields} FROM wilson_filtered_news WHERE 1=1"
            filters = []
            
            if 'start_date' in request.args and request.args['start_date']:
                query += " AND publish_date >= %s"
                filters.append(request.args['start_date'])
            
            if 'end_date' in request.args and request.args['end_date']:
                query += " AND publish_date <= %s"
                filters.append(request.args['end_date'])
            
            if 'filters' in request.args and request.args['filters']:
                filter_pairs = request.args['filters'].split(",")
                for pair in filter_pairs:
                    key, value = pair.split("=")
                    if key in valid_fields:
                        query += f" AND {key} = %s"
                        filters.append(value)
            
            query += " ORDER BY publish_date DESC"
            cursor.execute(query, tuple(filters))
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            return jsonify({"google_cse_results": results})
        except pymysql.MySQLError as e:
            return jsonify({"error": str(e)}), 500



##############################################
# 2-1-1. PPT文章情感分析API
##############################################
class PttArticles(Resource):
    def get(self, keyword):
        """
        查詢特定關鍵字的所有文章標題、日期及 ID
        ---
        parameters:
          - name: keyword
            in: path
            type: string
            required: true
            description: 請輸入欲查詢的關鍵字 (MoMo or PChome)
        responses:
          200:
            description: 返回查詢的文章列表
        tags:
          - PTT 網購論壇數據
        """
        try:
            conn = pymysql.connect(**db_config)
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute(
                "SELECT id, article_title, article_date FROM judy_db WHERE keyword = %s",
                (keyword,),
            )
            articles = cursor.fetchall()
            cursor.close()
            conn.close()

            return jsonify({"keyword": keyword, "articles": articles})

        except pymysql.MySQLError as e:
            return jsonify({"error": str(e)}), 500


class PttArticleCount(Resource):
    def get(self, keyword):
        """
        查詢特定關鍵字的文章數量
        ---
        parameters:
          - name: keyword
            in: path
            type: string
            required: true
            description: 請輸入欲查詢的關鍵字(MoMo or PChome)
        responses:
          200:
            description: 返回查詢的文章數量
        tags:
          - PTT 網購論壇數據
        """
        try:
            conn = pymysql.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM judy_db WHERE keyword = %s", (keyword,)
            )
            count = cursor.fetchone()[0]
            cursor.close()
            conn.close()

            return jsonify({"keyword": keyword, "count": count})

        except pymysql.MySQLError as e:
            return jsonify({"error": str(e)}), 500


class PttArticlesByDate(Resource):
    def get(self, date):
        """
        查詢特定日期的所有文章標題、關鍵字及 ID
        ---
        parameters:
          - name: date
            in: path
            type: string
            required: true
            description: 查詢的日期，格式為 'YYYY-MM-DD'
        responses:
          200:
            description: 返回查詢的文章列表
        tags:
          - PTT 網購論壇數據            
        """
        try:
            conn = pymysql.connect(**db_config)
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute(
                "SELECT id, article_title, keyword FROM judy_db WHERE article_date = %s",
                (date,),
            )
            articles = cursor.fetchall()
            cursor.close()
            conn.close()

            if articles:
                return jsonify({"date": date, "articles": articles})
            else:
                return jsonify({"error": "No articles found for this date"}), 404

        except pymysql.MySQLError as e:
            return jsonify({"error": str(e)}), 500


class PttArticleByIdWithSentiment(Resource):
    def get(self, article_id):
        """
        透過 ID 查詢文章內容、日期、標題及情感分數
        ---
        parameters:
          - name: article_id
            in: path
            type: integer
            required: true
            description: 請輸入欲查詢的文章 ID
        responses:
          200:
            description: 返回查詢的文章資訊和情感分數
        tags:
          - PTT 網購論壇數據        
        """
        try:
            conn = pymysql.connect(**db_config)
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute(
                """
                SELECT id, article_title, article_date, article_content, keyword, sentiment_score
                FROM judy_db
                WHERE id = %s
            """,
                (article_id,),
            )
            article = cursor.fetchone()
            cursor.close()
            conn.close()

            if article:
                return jsonify(
                    {
                        "article_id": article["id"],
                        "article_title": article["article_title"],
                        "article_date": article["article_date"],
                        "article_content": article["article_content"],
                        "keyword": article["keyword"],
                        "sentiment_score": article["sentiment_score"],
                    }
                )
            else:
                return jsonify({"error": "Article not found"}), 404

        except pymysql.MySQLError as e:
            return jsonify({"error": str(e)}), 500


##############################################
# 2-1-2. 新增查看 & 下載圖片的 API
##############################################
# API支援查詢路徑下圖片，故需另外列出"圖片目錄陣列"，若有新增圖片在其他路徑，就需要另外再寫。
PICTURE_DIRS = [
    "/home//one_stop/picture",
    "/home/圖片/",  
]


class PictureList(Resource):
    def get(self):
        """
        列出所有圖片名稱
        ---
        responses:
          200:
            description: 返回目錄中所有圖片的檔名
        tags:
          - 視覺化圖形彙整
        """
        result = []

        for PICTURE_DIR in PICTURE_DIRS:
            if not os.path.exists(PICTURE_DIR):
                continue

            files = os.listdir(PICTURE_DIR)
            image_extensions = (".png", ".jpg", ".jpeg", ".gif")
            image_files = [f for f in files if f.lower().endswith(image_extensions)]
            result.extend(image_files)
        if not result:
            return jsonify({"error": "No pictures found in all directories."}), 404

        return jsonify({"pictures": result})


class Picture(Resource):
    def get(self, filename):
        """
        下載或顯示指定圖片
        ---
        parameters:
          - name: filename
            in: path
            type: string
            required: true
            description: 圖片檔名
        responses:
          200:
            description: 直接傳回該圖片檔
        tags:
          - 視覺化圖形彙整        
        """
        for picture_dir in PICTURE_DIRS:
            file_path = os.path.join(picture_dir, filename)
            if os.path.exists(file_path):
                return send_from_directory(picture_dir, filename)

        return jsonify({"error": f"File not found: {filename}"}), 404


##############################################
# 2-2-1. 搜尋結果準確度API
##############################################
def connect_to_db():
    return pymysql.connect(**db_config)


def create_table(db_connection, platform):
    with db_connection.cursor() as cursor:
        cursor.execute(
            f"CREATE TABLE IF NOT EXISTS `yuting_{platform}_dynamique_search_accuracy` (timestamp DATETIME, keyword TEXT, search_result TEXT)"
        )
    db_connection.commit()


def check_table_has_data(db_connection, platform, keyword):
    with db_connection.cursor() as cursor:
        cursor.execute(
            f"SELECT COUNT(*) FROM `yuting_{platform}_dynamique_search_accuracy` WHERE keyword = %s",
            (keyword,),
        )
        return cursor.fetchone()[0] > 0


def insert_data(db_connection, platform, keyword, data):
    with db_connection.cursor() as cursor:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for row in data:
            cursor.execute(
                f"""
            INSERT INTO `yuting_{platform}_dynamique_search_accuracy` (timestamp, keyword, search_result)
            VALUES (%s, %s, %s)
            """,
                (timestamp, keyword, row["search_result"]),
            )
    db_connection.commit()


def crawler_momo(db_connection, keyword, max_pages=1):
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(service=service, options=options)
    all_results = []
    for page in range(1, max_pages + 1):
        driver.get(
            f"https://www.momoshop.com.tw/search/searchShop.jsp?keyword={keyword}&page={page}"
        )
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(3, 8))
        titles = driver.find_elements(By.CLASS_NAME, "prdName")
        results = [
            {"search_result": title.text}
            for title in titles
            if title.text.strip() != ""
        ]
        all_results.extend(results)
    driver.quit()

    # 在執行爬蟲後檢查資料庫是否已經有資料
    if check_table_has_data(db_connection, "momo", keyword):
        # 如果資料已存在，就只回傳爬蟲結果，不執行資料庫插入
        return all_results

    # 如果資料表中沒有資料，就將爬取的資料插入資料庫
    insert_data(db_connection, "momo", keyword, all_results)
    # 回傳爬取的最新資料
    return all_results


def crawler_pchome(db_connection, keyword, max_pages=1):
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(service=service, options=options)
    all_results = []
    for page in range(1, max_pages + 1):
        driver.get(f"https://24h.pchome.com.tw/search/?q={keyword}")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(5, 9))
        no_item = driver.find_elements(By.CLASS_NAME, "c-tipsBox")
        if no_item:
            no_data = [{"search_result": "No Relevant Item Exists"}]
            all_results.extend(no_data)
        else:
            titles = driver.find_elements(By.CLASS_NAME, "c-prodInfoV2__title")
            results = [
                {"search_result": title.text}
                for title in titles
                if title.text.strip() != ""
            ]
            all_results.extend(results)
    driver.quit()
    if check_table_has_data(db_connection, "pchome", keyword):
        return all_results
    insert_data(db_connection, "pchome", keyword, all_results)
    return all_results


def get_statistics(db_connection, platform, keyword):
    with db_connection.cursor() as cursor:
        cursor.execute(
            f"SELECT COUNT(*) FROM `yuting_{platform}_dynamique_search_accuracy` WHERE keyword = %s",
            (keyword,),
        )
        count = cursor.fetchone()[0]
    return {"keyword": keyword, "product_count": count}


def analyze_keyword_with_spacing(
    db_connection, platform, keyword, regex_pattern, exclude_terms
):
    with db_connection.cursor() as cursor:
        exclude_pattern = "|".join(exclude_terms)
        cursor.execute(
            f"""
            SELECT COUNT(*) FROM `yuting_{platform}_dynamique_search_accuracy`
            WHERE keyword = '{keyword}' and search_result REGEXP %s AND search_result NOT REGEXP %s
        """,
            (regex_pattern, exclude_pattern),
        )
        filtered_count = cursor.fetchone()[0]

        cursor.execute(
            f"SELECT COUNT(*) FROM `yuting_{platform}_dynamique_search_accuracy` WHERE keyword = %s",
            (keyword,),
        )
        total_count = cursor.fetchone()[0]

        return round(filtered_count / total_count, 4) if total_count > 0 else 0


def generate_regex_pattern(keyword):
    return r".*?".join(keyword)


class SearchProducts(Resource):
    def post(self):
        """根據指定商品關鍵字，計算MOMO與PChome搜尋結果準確度
        ---
        parameters:
          - name: keyword
            in: formData
            type: string
            required: true
            description: 查詢關鍵字
        responses:
          200:
            description: 商品統計數據
        tags:
          - 準確度計算: 平台搜尋結果準確度分析
        """
        keyword = request.form["keyword"]

        connection_to_db = connect_to_db()

        create_table(connection_to_db, "momo")
        create_table(connection_to_db, "pchome")

        if not check_table_has_data(connection_to_db, "momo", keyword):
            momo_data = crawler_momo(connection_to_db, keyword)
            insert_data(connection_to_db, "momo", keyword, momo_data)

        if not check_table_has_data(connection_to_db, "pchome", keyword):
            pchome_data = crawler_pchome(connection_to_db, keyword)
            insert_data(connection_to_db, "pchome", keyword, pchome_data)

        momo_stats = get_statistics(connection_to_db, "momo", keyword)
        pchome_stats = get_statistics(connection_to_db, "pchome", keyword)

        regex_pattern = generate_regex_pattern(keyword)
        exclude_terms = ["適用", "專用", "配件", "支援"]
        momo_precision = f"{float(analyze_keyword_with_spacing(connection_to_db, 'momo', keyword, regex_pattern, exclude_terms))*100}%"
        pchome_precision = f"{float(analyze_keyword_with_spacing(connection_to_db, 'pchome', keyword, regex_pattern, exclude_terms))*100}%"

        connection_to_db.close()

        return jsonify(
            {
                "keyword": keyword,
                "momo": {"product_count": momo_stats, "accuracy": momo_precision},
                "pchome": {"product_count": pchome_stats, "accuracy": pchome_precision},
            }
        )


##############################################
# 3-1. 建立 Dash 應用並掛載在同一個 Flask 上 / 準確度查詢
##############################################
dash_app = dash.Dash(
    __name__,
    server=app,
    url_base_pathname="/search_accuracy/",
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)

dash_app.layout = dbc.Container(
    [
        html.H1("PChome、momo商品搜尋結果準確度比較", className="text-center mt-4"),
        dcc.Input(
            id="input-keyword",
            type="text",
            placeholder="請輸入關鍵字",
            className="form-control",
        ),
        html.Button("查詢過去資料", id="search-history-button", className="btn btn-primary mt-2"),
        html.Button("即時查詢", id="search-live-button", className="btn btn-secondary mt-2 ml-2"),
        html.Div(id="search-result", className="mt-4"),
    ]
)



@dash_app.callback( 
    Output("search-result", "children"),
    [Input("search-history-button", "n_clicks"), Input("search-live-button", "n_clicks")],
    State("input-keyword", "value")
)
def update_search_result(history_clicks, live_clicks, keyword):
    if not keyword:
        return "請輸入商品關鍵字並點擊查詢"

    connection_to_db = connect_to_db()
    create_table(connection_to_db, "momo")
    create_table(connection_to_db, "pchome")

    # 定義共用變數
    result_divs = []

    # 查詢過去資料
    if history_clicks:
        # momo
        if check_table_has_data(connection_to_db, "momo", keyword):
            momo_stats = get_statistics(connection_to_db, "momo", keyword)
            # 取得 timestamp
            with connection_to_db.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT timestamp FROM yuting_momo_dynamique_search_accuracy
                    WHERE keyword = %s ORDER BY timestamp DESC LIMIT 1
                    """, 
                    (keyword,)
                )
                momo_timestamp = cursor.fetchone()

            regex_pattern = generate_regex_pattern(keyword)
            exclude_terms = ["適用", "專用", "配件", "支援"]
            momo_precision = f"{float(analyze_keyword_with_spacing(connection_to_db, 'momo', keyword, regex_pattern, exclude_terms))*100}%"
            
            result_divs.append(html.Div(
                [
                    html.H3(f"您搜尋的關鍵字：{keyword}"),
                    html.H4(
                        "MOMO 平台搜尋結果：", 
                        style={
                            'font-size': '20px', 
                            'font-weight': 'bold',
                            'margin-bottom': '5px'
                        }
                    ),
                    html.P(
                        f"◆ 商品數量：{momo_stats['product_count']}",
                        style={
                            'margin-left': '15px', 
                            'font-size': '18px'
                        }
                    ),
                    html.P(
                        f"◆ 搜尋結果準確度：{momo_precision}",
                        style={
                            'margin-left': '15px', 
                            'font-size': '18px'
                        }
                    ),
                    html.P(
                        f"（資料分析時間：{momo_timestamp[0] if momo_timestamp else '無紀錄'}）",
                        style={
                            'margin-left': '15px', 
                            'font-size': '16px', 
                            'color': '#555'
                        }
                    ),
                ],
                style={
                    'border': '1px solid #ccc', 
                    'border-radius': '10px', 
                    'padding': '15px', 
                    'margin': '20px 0',
                    'background-color': '#f9f9f9'
                }
            ))

        else:
            result_divs.append(html.P("MOMO 無歷史資料，請點擊 '即時查詢' 以獲取最新資料。"))

        # pchome
        if check_table_has_data(connection_to_db, "pchome", keyword):
            pchome_stats = get_statistics(connection_to_db, "pchome", keyword)
            with connection_to_db.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT timestamp FROM yuting_pchome_dynamique_search_accuracy
                    WHERE keyword = %s ORDER BY timestamp DESC LIMIT 1
                    """, 
                    (keyword,)
                )
                pchome_timestamp = cursor.fetchone()

            regex_pattern = generate_regex_pattern(keyword)
            exclude_terms = ["適用", "專用", "配件", "支援"]
            pchome_precision = f"{float(analyze_keyword_with_spacing(connection_to_db, 'pchome', keyword, regex_pattern, exclude_terms))*100}%"
            
            
            result_divs.append(html.Div(
                [
                    html.H4(
                        "PChome 平台搜尋結果：", 
                        style={
                            'font-size': '20px', 
                            'font-weight': 'bold',
                            'margin-bottom': '5px'
                        }
                    ),
                    html.P(
                        f"◇ 商品數量：{pchome_stats['product_count']}",
                        style={
                            'margin-left': '15px', 
                            'font-size': '18px'
                        }
                    ),
                    html.P(
                        f"◇ 搜尋結果準確度：{pchome_precision}",
                        style={
                            'margin-left': '15px', 
                            'font-size': '18px'
                        }
                    ),
                    html.P(
                        f"（資料分析時間：{pchome_timestamp[0] if pchome_timestamp else '無紀錄'}）",
                        style={
                            'margin-left': '15px', 
                            'font-size': '16px', 
                            'color': '#555'
                        }
                    ),
                ],
                style={
                    'border': '1px solid #ccc', 
                    'border-radius': '10px', 
                    'padding': '15px', 
                    'margin': '20px 0',
                    'background-color': '#f9f9f9'
                }
            ))
        else:
            result_divs.append(html.P("PChome 無歷史資料，請點擊 '即時查詢' 以獲取最新資料。"))

    # 即時查詢
    if live_clicks:
        momo_data = crawler_momo(connection_to_db, keyword)
        pchome_data = crawler_pchome(connection_to_db, keyword)
        momo_count = len(momo_data)
        pchome_count = len(pchome_data)
        
        regex_pattern = generate_regex_pattern(keyword)
        exclude_terms = ["適用", "專用", "配件", "支援"]
        momo_precision = f"{float(analyze_keyword_with_spacing(connection_to_db, 'momo', keyword, regex_pattern, exclude_terms))*100}%"
        pchome_precision = f"{float(analyze_keyword_with_spacing(connection_to_db, 'pchome', keyword, regex_pattern, exclude_terms))*100}%"

        # 顯示即時查詢結果
        result_divs.append(html.Div(
    [
        html.H4(
            f"即時查詢 - 關鍵字：{keyword}", 
            style={
                'font-size': '22px', 
                'font-weight': 'bold', 
                'margin-bottom': '10px'
            }
        ),
        html.P(
            f"◆ MOMO 商品數量：{momo_count}，準確度：{momo_precision}",
            style={
                'font-size': '18px', 
                'margin': '5px 0'
            }
        ),
        html.P(
            f"◇ PChome 商品數量：{pchome_count}，準確度：{pchome_precision}",
            style={
                'font-size': '18px', 
                'margin': '5px 0'
            }
        )
    ],
    style={
        'border': '1px solid #ccc', 
        'border-radius': '10px', 
        'padding': '15px', 
        'margin': '20px 0',
        'background-color': '#f9f9f9'
    }
))
    connection_to_db.close()
    return html.Div(result_divs)



##############################################
# 3-2. 建立 Dash 應用並掛載在同一個 Flask 上 / 動態分散圖 (PTT) 查看分數對應的ID
##############################################
dash_app_2 = dash.Dash(
    __name__,
    server=app,  # 使用同一個 Flask server
    url_base_pathname="/plotly_chart/",  # Dash 的路由前綴 (可自訂)
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)


def fetch_data():
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("SELECT id, sentiment_score FROM judy_db")
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return pd.DataFrame(data, columns=["ID", "Sentiment Score"])


df = fetch_data()

dash_app_2.layout = dbc.Container(
    [
        html.H1("文章情感分析 (散點圖)", className="text-center mt-4"),
        html.P("點擊散點圖上的分數，查看對應的文章 ID", className="text-center"),
        dcc.Graph(
            id="sentiment-scatter",
            figure=px.scatter(
                df,
                x="Sentiment Score",
                y="ID",
                title="文章情感分數與 ID 分佈",
                color="Sentiment Score",
                color_continuous_scale="Blues",
                hover_data=["ID"],
            ),
        ),
        html.H3("符合的文章 ID：", className="mt-4"),
        html.P("(請點擊圖表中的分數)", id="selected-score"),
        html.Div(id="id-list", className="mt-2"),
    ]
)


@dash_app_2.callback(
    [Output("selected-score", "children"), Output("id-list", "children")],
    [Input("sentiment-scatter", "clickData")],
)
def display_selected_ids(clickData):
    if not clickData:
        return "(請點擊圖表中的分數)", ""
    selected_score = clickData["points"][0]["x"]
    filtered_df = df[df["Sentiment Score"] == selected_score]
    id_list = ", ".join(map(str, filtered_df["ID"].tolist()))
    return f"選擇的分數：{selected_score}", f"對應的 ID：{id_list}"


##############################################
# 4. 頁面導引
##############################################
@app.route("/")
def index():
    # 只保留以下連結
    return """
    <h1>MOMO vs PChome 資訊比較查詢</h1>
    <p>請點選以下連結：</p>
    <ul>
        <li><a href="/swagger-ui/">API 文件 (Swagger)</a></li>
        <li><a href="/plotly_chart/">動態分散圖 (PTT) 查看分數對應的ID</a></li>
        <li><a href="/search_accuracy/">搜尋結果準確度</a></li>
    </ul>
    """


##############################################
# 新增路由
##############################################
api.add_resource(MomoMonthlyResource, "/momo_monthly_revenue")
api.add_resource(PchomeMonthlyResource, "/pchome_monthly_revenue")
api.add_resource(NewsResource, "/news")
api.add_resource(GetCSEOutcomes, "/get_cse_outcomes")
api.add_resource(PttArticles, "/articles/<string:keyword>")
api.add_resource(PttArticleCount, "/article_count/<string:keyword>")
api.add_resource(PttArticlesByDate, "/articles_by_date/<string:date>")
api.add_resource(
    PttArticleByIdWithSentiment, "/article_by_id_with_sentiment/<int:article_id>"
)
api.add_resource(PictureList, "/pictures")
api.add_resource(Picture, "/pictures/<string:filename>")
api.add_resource(SearchProducts, "/search_accuracy")

##############################################
# 5. 啟動
##############################################
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5555, debug=True)
