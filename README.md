# Hệ thống Đồng bộ Dữ liệu MySQL sang SQL Server qua RabbitMQ 🔄

Dự án này triển khai một pipeline dữ liệu hoàn chỉnh, sử dụng mô hình **Polling Publisher** để theo dõi các thay đổi trong database MySQL và mô hình **Consumer** để ghi những thay đổi đó vào database SQL Server một cách bất đồng bộ qua RabbitMQ.

Đây là một giải pháp hiệu quả để đồng bộ dữ liệu gần-thời-gian-thực, đặc biệt hữu ích khi ứng dụng chỉ có quyền đọc (`SELECT`) đối với database nguồn.

## Vấn đề cần giải quyết 🎯

Trong nhiều hệ thống lớn, các ứng dụng mới cần truy cập và xử lý dữ liệu từ các database cũ (legacy). Dự án này giải quyết bài toán trên bằng cách tạo ra hai service độc lập:
1.  **`polling-app` (Publisher):** Định kỳ "hỏi thăm" MySQL để tìm các bản ghi mới và gửi thông tin vào RabbitMQ.
2.  **`consumer-app` (Consumer):** Lắng nghe tin nhắn từ RabbitMQ và ghi dữ liệu tương ứng vào SQL Server.

Mô hình này giúp tách biệt logic đọc và ghi, tăng tính ổn định và khả năng mở rộng cho hệ thống.

## Kiến trúc hệ thống 🏗️

Luồng hoạt động của dữ liệu từ nguồn đến đích được thể hiện qua sơ đồ sau:

```
+------------------+   1. SELECT * FROM...    +-------------------+
|                  | <----------------------- |                   |
|  DATABASE MYSQL  |                          |    POLLING APP    |
|  (Nguồn dữ liệu)  |   2. Publish JSON Msg    | (Publisher)       |
|                  | -----------------------> |                   |
+------------------+                          +-------------------+
                                                        |
                                                        v
+------------------+      3. Route & Queue Msg      +-------------------+
|                  | <----------------------------- |                   |
|     RABBITMQ     |                                |   CONSUMER APP    |
| (Message Broker) |      4. Consume Msg            |  (Subscriber)     |
|                  | -----------------------------> |                   |
+------------------+                                +-------------------+
                                                        |
                                                        | 5. INSERT INTO...
                                                        v
                                                +---------------------+
                                                |                     |
                                                |  DATABASE SQL SERVER|
                                                |    (Đích dữ liệu)   |
                                                |                     |
                                                +---------------------+
```

## Công nghệ sử dụng 🛠️

* **Ngôn ngữ:** Python 3.11 🐍
* **Databases:**
    * Nguồn: MySQL 8.0 🐬
    * Đích: MS SQL Server 2019 🗄️
* **Message Broker:** RabbitMQ 3.9 🐇
* **Containerization:** Docker & Docker Compose 🐳
* **Thư viện Python chính:**
    * `pika`: Client cho RabbitMQ.
    * `mysql-connector-python`: Client cho MySQL.
    * `pyodbc`: Client cho SQL Server (yêu cầu ODBC Driver).

## Cấu trúc thư mục 📁

```
.
├── docker-compose.yml        # File điều phối các container (MySQL, RabbitMQ, Poller, Consumer...)
├── mock_data/
│   └── TPHHLC1.xlsx          # File dữ liệu mẫu đầu vào
├── mysql_setup/
│   ├── init.sql              # Script khởi tạo user và phân quyền cho MySQL
│   └── xlsx_to_mysql.py      # Script để nạp dữ liệu từ file Excel vào MySQL
├── polling_app/
│   ├── Dockerfile            # Thiết kế image cho ứng dụng Polling (Publisher)
│   ├── poller.py             # Logic chính của Polling App
│   └── requirements.txt      # Thư viện Python cho Polling App
├── consumer_app/
│   ├── Dockerfile            # Thiết kế image cho ứng dụng Consumer (Subscriber)
│   ├── consumer.py           # Logic chính của Consumer App
│   └── requirements.txt      # Thư viện Python cho Consumer App
└── README.md                 # File hướng dẫn này
```

## Hướng dẫn Cài đặt và Khởi chạy ⚙️

#### Yêu cầu tiên quyết 📋
* [Docker](https://www.docker.com/get-started)
* [Docker Compose](https://docs.docker.com/compose/install/)
* Git

#### Các bước cài đặt 🚀

1.  **Clone repository về máy:**
    ```bash
    git clone [URL_GITHUB_CUA_BAN]
    cd [TEN_THU_MUC_DU_AN]
    ```

2.  **Khởi chạy các services nền tảng:**
    Chạy lệnh sau để khởi động MySQL, RabbitMQ, Polling App và Consumer App.
    ```bash
    docker-compose up -d --build
    ```
    *Lưu ý: Quá trình khởi động lần đầu có thể mất vài phút, đặc biệt là SQL Server.*

3.  **Chuẩn bị Database Đích (SQL Server):**
    * Sau khi các container đã chạy, bạn cần kết nối vào SQL Server để tạo bảng sẽ nhận dữ liệu.
    * Dùng một công cụ quản lý DB (Azure Data Studio, DBeaver, etc.) để kết nối tới:
        * **Server:** `localhost,1433`
        * **User:** `sa`
        * **Password:** `yourStrong(!)Password` (mật khẩu trong `docker-compose.yml`)
    * Chạy script SQL sau để tạo bảng (bạn có thể tùy chỉnh cho phù hợp):
      ```sql
      CREATE TABLE steel_production_logs (
          c DECIMAL(10, 4), si DECIMAL(10, 4), mn DECIMAL(10, 4), s DECIMAL(10, 4), p DECIMAL(10, 4),
          ti DECIMAL(10, 4), temp INT, feo DECIMAL(10, 3), sio2 DECIMAL(10, 3), al2o3 DECIMAL(10, 3),
          cao DECIMAL(10, 3), mgo DECIMAL(10, 3), r2 DECIMAL(10, 2), na2o DECIMAL(10, 3),
          k2o DECIMAL(10, 3), tio2 DECIMAL(10, 3), mno DECIMAL(10, 2), hskt DECIMAL(10, 3),
          classifyname NVARCHAR(100), testpatterncode NVARCHAR(100), testpatternname NVARCHAR(100),
          productiondate DATE, shiftname NVARCHAR(50), inputtime DATETIME, patterntime NVARCHAR(50)
      );
      ```

4.  **Nạp dữ liệu ban đầu vào MySQL:**
    Chạy script Python sau từ máy của bạn để đọc file Excel và đẩy dữ liệu vào container MySQL.
    ```bash
    python ./mysql_setup/xlsx_to_mysql.py
    ```
    *Ngay sau khi chạy xong, `polling-app` sẽ phát hiện dữ liệu mới này và bắt đầu pipeline.*

## Cách sử dụng và kiểm tra ✅

#### 1. Kiểm tra trạng thái các container 📈
```bash
docker-compose ps
```
Bạn sẽ thấy các container `rabbitmq`, `polling-app`, `consumer-app`, `sql-server-db` đều đang ở trạng thái `up` hoặc `running (healthy)`.

#### 2. Xem log của Poller và Consumer 📜
* **Xem Poller gửi tin nhắn:**
    ```bash
    docker-compose logs -f polling-app
    ```
* **Xem Consumer nhận và ghi tin nhắn:**
    ```bash
    docker-compose logs -f consumer-app
    ```

#### 3. Kiểm tra tin nhắn trong RabbitMQ 🐇
1.  Mở trình duyệt: `http://localhost:15672`
2.  Đăng nhập: `user` / `password`.
3.  Vào tab **Queues**, bạn sẽ thấy `sql_server_writer_queue` đang nhận và xử lý tin nhắn.

#### 4. Kiểm tra dữ liệu trong SQL Server 🎯
Kết nối lại vào SQL Server và chạy lệnh `SELECT * FROM steel_production_logs;` để xác nhận dữ liệu đã được ghi vào thành công.

## Mẹo gỡ lỗi 💡
File `polling_app/state/last_timestamp.txt` lưu lại thời điểm cuối cùng mà `polling-app` đã làm việc. Nếu bạn muốn `polling-app` đồng bộ lại toàn bộ dữ liệu từ MySQL, chỉ cần **xóa nội dung** trong file này và lưu lại. Ở lần chạy tiếp theo, nó sẽ lấy lại tất cả dữ liệu.

## Cấu hình 🔧
Các cấu hình được quản lý qua biến môi trường trong file `docker-compose.yml`:

| Service       | Biến môi trường           | Mô tả                                            |
|---------------|---------------------------|--------------------------------------------------|
| `polling-app` | `MYSQL_HOST`              | Host của MySQL nguồn                             |
| `polling-app` | `MYSQL_USER`              | User của MySQL nguồn                             |
| `polling-app` | `MYSQL_PASSWORD`          | Password của MySQL nguồn                         |
| `polling-app` | `RABBITMQ_HOST`           | Host của RabbitMQ                                |
| `polling-app` | `POLLING_INTERVAL_SECONDS`| Khoảng thời gian nghỉ giữa các lần polling (giây) |
| `consumer-app`| `RABBITMQ_HOST`           | Host của RabbitMQ                                |
| `consumer-app`| `SQL_SERVER_HOST`         | Host của SQL Server đích                         |
| `consumer-app`| `SQL_SERVER_DB`           | Database của SQL Server đích                     |
| `consumer-app`| `SQL_SERVER_USER`         | User của SQL Server đích                         |
| `consumer-app`| `SQL_SERVER_PASS`         | Password của SQL Server đích                     |
