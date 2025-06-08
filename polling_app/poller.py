import pika
import mysql.connector
import os
import time
import json
import logging
import datetime

# --- Cấu hình logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Đọc cấu hình từ biến môi trường ---
MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_USER = os.getenv('MYSQL_USER', 'polluser')
MYSQL_PASS = os.getenv('MYSQL_PASSWORD', 'pollpassword')
MYSQL_DB = os.getenv('MYSQL_DB', 'productiondb')
MYSQL_TABLE = os.getenv('MYSQL_TABLE', 'steel_production_logs')

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'user')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASS', 'password')
RABBITMQ_EXCHANGE = os.getenv('RABBITMQ_EXCHANGE', 'data_sync_exchange')
POLLING_INTERVAL = int(os.getenv('POLLING_INTERVAL_SECONDS', 30))

# --- Quản lý trạng thái Polling ---
STATE_FILE_PATH = 'state/last_timestamp.txt'

def get_last_timestamp():
    """Đọc timestamp của lần xử lý cuối cùng từ file."""
    try:
        with open(STATE_FILE_PATH, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        # Nếu file không tồn tại, trả về một mốc thời gian rất cũ
        return '1970-01-01 00:00:00'

# def save_last_timestamp(timestamp):
#     """Lưu timestamp cuối cùng đã xử lý vào file."""
#     os.makedirs(os.path.dirname(STATE_FILE_PATH), exist_ok=True)
#     with open(STATE_FILE_PATH, 'w') as f:
#         # Chuyển đổi datetime object thành string trước khi ghi
#         f.write(timestamp.strftime('%Y-%m-%d %H:%M:%S'))

def save_last_timestamp(timestamp):
    """Lưu timestamp cuối cùng đã xử lý vào file.
       Hàm này xử lý được cả đầu vào là datetime object hoặc string.
    """
    os.makedirs(os.path.dirname(STATE_FILE_PATH), exist_ok=True)
    with open(STATE_FILE_PATH, 'w') as f:
        # Kiểm tra xem timestamp có phải là đối tượng datetime không
        if isinstance(timestamp, datetime.datetime):
            # Nếu đúng, định dạng nó thành chuỗi
            f.write(timestamp.strftime('%Y-%m-%d %H:%M:%S'))
        else:
            # Nếu nó đã là một chuỗi (hoặc kiểu khác), ghi thẳng nó ra file
            f.write(str(timestamp))

def json_converter(o):
    """Hàm tùy chỉnh để chuyển đổi các kiểu dữ liệu không thể serialize."""
    if isinstance(o, datetime):
        return o.isoformat()
    # Thêm các kiểu dữ liệu khác nếu cần
    # if isinstance(o, decimal.Decimal):
    #     return float(o)
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")

def poll_database_and_publish():
    """Hàm chính thực hiện polling và publish."""
    mysql_conn = None
    rabbitmq_conn = None
    last_processed_time = get_last_timestamp()
    
    try:
        # --- Kết nối MySQL ---
        logging.info("Connecting to MySQL...")
        mysql_conn = mysql.connector.connect(
            host=MYSQL_HOST,
            # port=3307, # chỉ sử dụng khi chạy thủ công file này
            user=MYSQL_USER,
            password=MYSQL_PASS,
            database=MYSQL_DB
        )
        cursor = mysql_conn.cursor(dictionary=True) # dictionary=True để lấy kết quả dạng dict
        
        query = f"SELECT * FROM {MYSQL_TABLE} WHERE inputtime > %s ORDER BY inputtime ASC"
        cursor.execute(query, (last_processed_time,))
        records = cursor.fetchall()
        
        if not records:
            logging.info(f"No new records found since {last_processed_time}.")
            return

        logging.info(f"Found {len(records)} new records.")

        # --- Kết nối RabbitMQ ---
        logging.info("Connecting to RabbitMQ...")
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
        rabbitmq_conn = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials))
        channel = rabbitmq_conn.channel()
        
        # Khai báo exchange, nếu chưa tồn tại sẽ được tạo
        channel.exchange_declare(exchange=RABBITMQ_EXCHANGE, exchange_type='fanout', durable=True)

        # --- Gửi từng record lên RabbitMQ ---
        new_latest_timestamp = None
        for record in records:
            message = json.dumps(record, default=json_converter)
            channel.basic_publish(
                exchange=RABBITMQ_EXCHANGE,
                routing_key='', # fanout exchange không cần routing key
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                ))
            logging.info(f"Published message for record with inputtime: {record['inputtime']}")
            new_latest_timestamp = record['inputtime']

        # --- Cập nhật trạng thái ---
        if new_latest_timestamp:
            save_last_timestamp(new_latest_timestamp)
            logging.info(f"State updated. New latest timestamp is {new_latest_timestamp}")

    except mysql.connector.Error as err:
        logging.error(f"MySQL Error: {err}")
    except pika.exceptions.AMQPConnectionError as err:
        logging.error(f"RabbitMQ Connection Error: {err}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    finally:
        if cursor:
            cursor.close()
        if mysql_conn and mysql_conn.is_connected():
            mysql_conn.close()
            logging.info("MySQL connection closed.")
        if rabbitmq_conn and rabbitmq_conn.is_open:
            rabbitmq_conn.close()
            logging.info("RabbitMQ connection closed.")


def main():
    """Vòng lặp polling chính."""
    logging.info("Starting Polling Service...")
    # Chờ một chút để các service khác khởi động hoàn toàn
    time.sleep(15) 
    
    while True:
        poll_database_and_publish()
        logging.info(f"Sleeping for {POLLING_INTERVAL} seconds...")
        time.sleep(POLLING_INTERVAL)

if __name__ == "__main__":
    main()