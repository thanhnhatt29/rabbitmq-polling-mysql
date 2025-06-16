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
<p align="center">
  <img src="images\flowchart.png">
</p>

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
├── docker-compose.yml        # File điều phối các container (RabbitMQ)
├── 3. polling_app/
│   ├── poller.py             # Logic chính của Polling App
│   ├── requirements.txt      # Thư viện Python cho Polling App
│   └── state/
│       └── last_timestamp.txt # File lưu trạng thái lần cuối polling
├── 4. consumer_app/
│   ├── consumer.py           # Logic chính của Consumer App
│   └── requirements.txt      # Thư viện Python cho Consumer App
└── README.md                 
```

## Hướng dẫn Cài đặt và Khởi chạy ⚙️

#### Yêu cầu tiên quyết 📋
* [Docker](https://www.docker.com/get-started)
* [Docker Compose](https://docs.docker.com/compose/install/)
* Git

#### Các bước cài đặt 🚀

1.  **Clone repository về máy:**
    Clone repository hoặc tải và giải nén mã nguồn vào một thư mục trên máy của bạn.

2.  **Khởi chạy các services nền tảng:**
    Mở terminal trong thư mục gốc của dự án và chạy lệnh sau để khởi động RabbitMQ.
    ```bash
    docker-compose up -d
    ```

3.  **Cài đặt thư viện Python:**
    Mở hai cửa sổ terminal riêng biệt. Trong mỗi cửa sổ, di chuyển vào thư mục tương ứng và cài đặt các gói cần thiết:

    * **Terminal 1 (cho Poller):**
        ```bash
        cd polling_app
        pip install -r requirements.txt
        ```

    * **Terminal 2 (cho Consumer):**
        ```bash
        cd consumer_app
        pip install -r requirements.txt
        ```

4.  **Chạy ứng dụng:**
    Bây giờ, hãy khởi động các script trong hai terminal đã mở:

    * **Trong Terminal 1 (Poller):**
        ```bash
        python poller.py
        ```

    * **Trong Terminal 2 (Consumer):**
        ```bash
        python consumer.py
        ```
    Hệ thống bây giờ đã hoạt động. `poller.py` sẽ bắt đầu truy vấn MySQL và gửi dữ liệu mới tới RabbitMQ, và `consumer.py` sẽ nhận và ghi chúng vào SQL Server.


## Cách sử dụng và kiểm tra ✅

#### 1. Xem log của Poller và Consumer 📜
Khi bạn chạy các script `poller.py` và `consumer.py` thủ công, log hoạt động sẽ được hiển thị trực tiếp trên cửa sổ terminal của chúng.
* Terminal của **Poller** sẽ hiển thị các thông báo như "Connecting to MySQL...", "Found X new records.", "Published message...".
* Terminal của **Consumer** sẽ hiển thị các thông báo như "Waiting for messages.", "Received new message.", "Successfully inserted record...".

#### 2. Kiểm tra tin nhắn trong RabbitMQ 🐇
1.  Mở trình duyệt và truy cập: `http://localhost:15672`
2.  Đăng nhập với tài khoản: `user` / `password`.
3.  Vào tab **Queues**, bạn sẽ thấy `sql_server_writer_queue` đang nhận và xử lý tin nhắn.

#### 3. Kiểm tra dữ liệu trong SQL Server 🎯
Kết nối vào SQL Server của bạn bằng một công cụ quản lý DB (như Azure Data Studio, DBeaver). Chạy lệnh sau để xác nhận dữ liệu đã được ghi thành công:
```sql
SELECT * FROM steel_production_logs;
```
*Lưu ý: Bảng `steel_production_logs` sẽ được tự động tạo bởi `consumer.py` trong lần đầu tiên nhận được tin nhắn nếu nó chưa tồn tại.*

## Mẹo gỡ lỗi 💡
File `polling_app/state/last_timestamp.txt` lưu lại thời điểm cuối cùng (`InputTime`) mà `polling-app` đã xử lý. Nếu bạn muốn `polling-app` đồng bộ lại toàn bộ dữ liệu từ MySQL, chỉ cần **xóa nội dung** trong file này và lưu lại. Ở lần chạy tiếp theo, nó sẽ truy vấn tất cả dữ liệu từ mốc thời gian '1970-01-01 00:00:00'.

## Cấu hình 🔧
Các thông tin kết nối và cấu hình khác được quản lý trực tiếp trong các file Python (`poller.py`, `consumer.py`) dưới dạng biến môi trường hoặc giá trị mặc định. Bạn có thể chỉnh sửa các biến sau cho phù hợp với môi trường của mình:

| File           | Biến (Ví dụ)         | Mô tả                                        |
|----------------|----------------------|----------------------------------------------|
| `poller.py`    | `MYSQL_HOST`         | Host của MySQL nguồn                         |
| `poller.py`    | `MYSQL_USER`         | User của MySQL nguồn                         |
| `poller.py`    | `MYSQL_PASS`         | Password của MySQL nguồn                     |
| `poller.py`    | `RABBITMQ_HOST`      | Host của RabbitMQ                            |
| `poller.py`    | `POLLING_INTERVAL`   | Khoảng thời gian nghỉ giữa các lần polling  |
| `consumer.py`  | `RABBITMQ_HOST`      | Host của RabbitMQ                            |
| `consumer.py`  | `SQL_SERVER_HOST`    | Host của SQL Server đích                     |
| `consumer.py`  | `SQL_SERVER_DB`      | Database của SQL Server đích                 |
| `consumer.py`  | `SQL_SERVER_USER`    | User của SQL Server đích                     |
| `consumer.py`  | `SQL_SERVER_PASS`    | Password của SQL Server đích                 |