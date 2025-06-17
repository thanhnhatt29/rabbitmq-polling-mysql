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


## Hướng Mở Rộng và Phát Triển 🚀

Kiến trúc hiện tại là một nền tảng vững chắc. Để phát triển hệ thống có thể đồng bộ hóa nhiều bảng hoặc toàn bộ database một cách linh hoạt và mạnh mẽ hơn, ta có thể cân nhắc các hướng cải tiến sau:

### 1. Chuyển sang Cấu hình Động (Config-driven)
Thay vì hard-code tên bảng và các tham số trong code, hãy sử dụng một file cấu hình tập trung (ví dụ: `config.yaml`). File này sẽ định nghĩa danh sách các bảng cần đồng bộ và các thông tin liên quan (như cột timestamp). Điều này giúp hệ thống trở nên linh hoạt, dễ dàng thêm/bớt bảng mà không cần sửa đổi mã nguồn.

### 2. Nâng cấp Quản lý Trạng thái
Mở rộng file `state/last_timestamp.txt` thành một file JSON (ví dụ: `state.json`) để lưu `timestamp` cuối cùng cho **từng bảng riêng biệt**. Điều này đảm bảo mỗi luồng đồng bộ hóa của từng bảng được theo dõi một cách độc lập.

### 3. Sử dụng Định tuyến Thông minh trong RabbitMQ
Chuyển từ `fanout` exchange (gửi cho tất cả) sang **`direct` exchange**.
* **Poller** sẽ gửi message với `routing_key` là **tên của bảng nguồn**.
* **Consumer** sẽ lắng nghe trên các `routing_key` tương ứng để biết dữ liệu nhận được thuộc về bảng nào, từ đó ghi vào bảng đích một cách chính xác.

### 4. Container hóa Toàn bộ Ứng dụng
Tạo `Dockerfile` cho cả `polling_app` và `consumer_app`. Cập nhật file `docker-compose.yml` để khởi chạy toàn bộ hệ thống (Poller, Consumer, RabbitMQ) chỉ bằng một lệnh duy nhất (`docker-compose up -d`). Điều này giúp đơn giản hóa việc triển khai, quản lý và đảm bảo môi trường chạy nhất quán.

### 5. Nâng cấp lên Change Data Capture (CDC)
Đối với các hệ thống yêu cầu đồng bộ gần như real-time và cần bắt cả sự kiện `UPDATE`, `DELETE` (không chỉ `INSERT`), hãy xem xét chuyển từ mô hình Polling sang **Change Data Capture (CDC)**.
* **Công cụ gợi ý:** **Debezium**.
* **Lợi ích:** Debezium đọc trực tiếp từ transaction log (binlog) của MySQL để bắt mọi thay đổi, giúp giảm tải đáng kể cho database nguồn và cung cấp dữ liệu với độ trễ cực thấp.