# consumer.py
import pika
import os
import time
import json
import logging
import pyodbc

# --- Cấu hình logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [Consumer] - %(levelname)s - %(message)s')

# --- Đọc cấu hình từ biến môi trường ---
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'user')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASS', 'password')
RABBITMQ_EXCHANGE = os.getenv('RABBITMQ_EXCHANGE', 'data_sync_exchange')
QUEUE_NAME = 'sql_server_writer_queue'

SQL_SERVER_HOST = os.getenv('SQL_SERVER_HOST')
# SQL_SERVER_PORT = os.getenv('SQL_SERVER_PORT', '1434')
SQL_SERVER_DB = os.getenv('SQL_SERVER_DB', 'productiondb')
SQL_SERVER_USER = os.getenv('SQL_SERVER_USER', 'sa')
SQL_SERVER_PASS = os.getenv('SQL_SERVER_PASS', 'HPDQ@1234')
SQL_SERVER_TABLE = os.getenv('SQL_SERVER_TABLE', 'steel_production_logs')

def ensure_table_exists(data_sample):
    """Tạo bảng nếu chưa tồn tại dựa trên sample data."""
    try:
        with get_sql_server_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                IF NOT EXISTS (
                    SELECT * FROM INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_NAME = '{SQL_SERVER_TABLE}'
                )
                BEGIN
                    CREATE TABLE {SQL_SERVER_TABLE} (
                        {', '.join(f"[{col}] NVARCHAR(MAX)" for col in data_sample.keys())}
                    )
                END
            """)
            conn.commit()
            # logging.info(f"Ensured table '{SQL_SERVER_TABLE}' exists.")
    except pyodbc.Error as e:
        logging.error(f"Failed to check/create table: {e}")


def get_sql_server_connection():
    """Tạo và trả về một kết nối tới SQL Server."""
    # server_address = f"{SQL_SERVER_HOST},{SQL_SERVER_PORT}" # Kết nối sẽ là "localhost,1434"

    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={SQL_SERVER_HOST};"
        f"DATABASE={SQL_SERVER_DB};"
        f"UID={SQL_SERVER_USER};"
        f"PWD={SQL_SERVER_PASS};"
    )
    return pyodbc.connect(conn_str)

def process_message(channel, method, properties, body):
    """Hàm callback được gọi mỗi khi có tin nhắn mới."""
    try:
        logging.info(f"Received new message. Routing key: {method.routing_key}")
        data = json.loads(body)
        
        # Bỏ qua các cột không cần thiết nếu có
        data.pop('id', None) # Bỏ cột id của MySQL
        
        # Đảm bảo bảng tồn tại (tạo nếu chưa có)
        ensure_table_exists(data)

        # Xây dựng câu lệnh INSERT một cách an toàn
        columns = ', '.join(f'[{col}]' for col in data.keys())
        placeholders = ', '.join(['?'] * len(data))
        sql_query = f"INSERT INTO {SQL_SERVER_TABLE} ({columns}) VALUES ({placeholders})"
        values = tuple(data.values())

        # Ghi vào SQL Server
        with get_sql_server_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql_query, values)
            conn.commit()
            logging.info(f"Successfully inserted record with inputtime: {data.get('InputTime')}")

        # Gửi xác nhận lại cho RabbitMQ rằng tin nhắn đã được xử lý xong
        channel.basic_ack(delivery_tag=method.delivery_tag)

    except json.JSONDecodeError as e:
        logging.error(f"Could not decode JSON: {e}")
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False) # Hủy và không xếp lại hàng
    except pyodbc.Error as e:
        logging.error(f"Database error: {e}")
        # Không ack/nack để tin nhắn có thể được xử lý lại sau khi lỗi DB được khắc phục
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def main():
    logging.info("Starting Consumer Service...")
    connection = None
    # Vòng lặp kết nối lại nếu RabbitMQ chưa sẵn sàng
    while True:
        try:
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials))
            channel = connection.channel()

            # Khai báo exchange (phải khớp với producer)
            channel.exchange_declare(exchange=RABBITMQ_EXCHANGE, exchange_type='fanout', durable=True)
            
            # Khai báo một queue bền vững để nhận tin nhắn
            result = channel.queue_declare(queue=QUEUE_NAME, durable=True)
            queue_name = result.method.queue
            
            # Đăng ký (bind) queue vào exchange
            channel.queue_bind(exchange=RABBITMQ_EXCHANGE, queue=queue_name)

            logging.info('Waiting for messages. To exit press CTRL+C')

            # Thiết lập cơ chế nhận tin nhắn
            channel.basic_consume(queue=queue_name, on_message_callback=process_message)
            
            # Bắt đầu lắng nghe
            channel.start_consuming()

        except pika.exceptions.AMQPConnectionError as e:
            logging.warning(f"Could not connect to RabbitMQ: {e}. Retrying in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            logging.error(f"Unhandled error: {e}. Restarting...")
            if connection and connection.is_open:
                connection.close()
            time.sleep(10)

if __name__ == '__main__':
    main()