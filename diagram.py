# diagram.py
from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.database import Mysql
from diagrams.onprem.queue import RabbitMQ 
from diagrams.custom import Custom
from diagrams.programming.framework import Fastapi 
from diagrams.programming.language import Python

with Diagram("Data Pipeline - Polling Architecture", show=False, filename="data_pipeline", direction="TB") as diag:
    
    with Cluster("Nguồn dữ liệu (Source)"):
        source_db = Mysql("DATABASE MYSQL")

    with Cluster("Polling Application"):
        polling_app = Python("Polling App\n(Python Container)")
    
    # Sử dụng class RabbitMQ đã import
    message_broker = RabbitMQ("RABBITMQ\n(Message Broker)")
    
    with Cluster("Hệ thống xử lý (Processing System)"):
        consumer_app = Fastapi("CONSUMER APP(S)")
        
        with Cluster("Đích (Destination)"):
            destination = Custom("DATABASE ĐÍCH,\nFILE, API...", "./api.png")

    # Định nghĩa luồng dữ liệu
    polling_app << Edge(label="1. SELECT query (10s/lần)", color="darkgreen", style="dashed") << source_db
    source_db >> Edge(label="2. Gửi data query", color="darkgreen") >> polling_app
    
    polling_app >> Edge(label="3. Gửi message JSON (Publish)", color="blue") >> message_broker
    
    message_broker >> Edge(label="4. Lắng nghe & nhận tin (Consume)", color="purple", style="dashed") >> consumer_app
    
    consumer_app >> Edge(label="5. Xử lý và ghi dữ liệu", color="darkorange") >> destination

print("Diagram 'data_pipeline.png' has been generated.")