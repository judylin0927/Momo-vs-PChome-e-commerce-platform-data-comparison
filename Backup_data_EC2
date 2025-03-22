#!/bin/bash

# 設定變數
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")  # 取得當前時間戳，格式為 YYYYMMDD_HHMMSS
BACKUP_DIR="/home/backup"      # 本地備份目錄 (備份文件將會存儲在 /home/backup 這個目錄下)
CSV_DIR="/home/one_stop/csv"   # CSV 文件所在目錄
PICTURE_DIR="/home/picture"  # 圖片文件所在目錄
EC2_USER="ubuntu"                   # EC2 伺服器的用戶名
EC2_HOST="ec2-????.ap-northeast-1.compute.amazonaws.com"  # EC2 伺服器的域名或 IP
EC2_PATH="/home/ubuntu/backup"  # EC2 伺服器上的備份目錄
KEY_PATH="/home/ONE_top.pem"   # 執行該程式碼需有鑰匙，才能連接 EC2 ( SSH 私鑰文件路徑 )

# 確保備份目錄存在
mkdir -p "$BACKUP_DIR"  # 如果備份目錄不存在，則創建它

# 啟用錯誤處理
set -e  # 如果任何命令執行失敗，則立即停止腳本

# 1️⃣ 備份 MariaDB（連接遠端資料庫）
echo "🔹 備份 MariaDB 中..."
mysqldump -h 主機 -P 3306 -u 使用者名稱 -p 密碼 --all-databases | gzip > "$BACKUP_DIR/mariadb_backup_$TIMESTAMP.sql.gz"
# 使用 mysqldump 備份遠端 MariaDB 的所有資料庫，並通過 gzip 壓縮，保存為 .sql.gz 文件

# 2️⃣ 壓縮 CSV 檔案（僅限 .csv）
echo "🔹 壓縮 CSV 檔案中..."
tar -czvf "$BACKUP_DIR/csv_backup_$TIMESTAMP.tar.gz" -C "$CSV_DIR" $(find "$CSV_DIR" -maxdepth 1 -type f -name "*.csv")
# 使用 tar 壓縮 CSV 目錄下的所有 .csv 文件，保存為 .tar.gz 文件

# 3️⃣ 壓縮圖片檔案
echo "🔹 壓縮圖片檔案中..."
tar -czvf "$BACKUP_DIR/picture_backup_$TIMESTAMP.tar.gz" -C "$PICTURE_DIR" .
# 使用 tar 壓縮圖片目錄下的所有文件，保存為 .tar.gz 文件

# 4️⃣ 傳輸到 EC2
echo "🔹 傳輸檔案到 EC2..."
scp -C -i "$KEY_PATH" "$BACKUP_DIR/mariadb_backup_$TIMESTAMP.sql.gz" \
    "$BACKUP_DIR/csv_backup_$TIMESTAMP.tar.gz" \
    "$BACKUP_DIR/picture_backup_$TIMESTAMP.tar.gz" \
    "$EC2_USER@$EC2_HOST:$EC2_PATH"
# 使用 scp 將備份文件傳輸到遠端 EC2 伺服器的指定目錄

echo "✅ 備份與傳輸完成！"
# 顯示完成訊息
