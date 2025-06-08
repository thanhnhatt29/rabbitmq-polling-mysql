# Sử dụng base image Python 3.11
FROM python:3.11-slim

# Cài đặt các gói cần thiết cho việc cài đặt ODBC driver
# Thêm gnupg và các công cụ khác để thêm kho lưu trữ của Microsoft
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# Thêm kho lưu trữ của Microsoft để cài đặt ODBC driver
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list

# Cập nhật lại danh sách gói và cài đặt Microsoft ODBC Driver 17 for SQL Server
RUN apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql17

# Thiết lập thư mục làm việc
WORKDIR /app

# Sao chép và cài đặt các thư viện Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép code của ứng dụng
COPY . .

# Lệnh sẽ được chạy khi container khởi động
CMD ["python", "consumer.py"]