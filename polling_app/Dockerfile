# Sử dụng base image Python chính thức
FROM python:3.11-slim

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Sao chép file requirements và cài đặt thư viện
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ code của ứng dụng
COPY . .

# Lệnh sẽ được chạy khi container khởi động
CMD ["python", "poller.py"]