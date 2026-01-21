import os
import shutil
import urllib.request
from diagrams import Diagram, Cluster, Edge
from diagrams.custom import Custom

# --- Configuration using PNGs for better compatibility ---
# I am using a generic AWS PNG logo which Graphviz can definitely render
ICON_URL = "https://raw.githubusercontent.com/mingrammer/diagrams/master/resources/aws/compute/ec2.png"
ICONS_DIR = "icons"
ICON_NAME = "aws_logo.png"
ICON_PATH = os.path.join(ICONS_DIR, ICON_NAME)

def download_icon():
    if not os.path.exists(ICONS_DIR):
        os.makedirs(ICONS_DIR)
    # Download the PNG to the local folder
    urllib.request.urlretrieve(ICON_URL, ICON_PATH)
    return ICON_PATH

try:
    # 1. Download the icon locally
    path = download_icon()

    # 2. Generate the Diagram
    with Diagram("Cloud-Native SaaS Architecture", filename="architecture", direction="LR", outformat="png", show=False, graph_attr={'fontsize': '16', 'bgcolor': 'white', 'pad': '0.5', 'rankdir': 'LR'}):
        with Cluster("Presentation Layer"):
            client_browser = Custom("Client Browser", path)
        with Cluster("Application Layer"):
            api_gateway = Custom("API Gateway", path)
            auth_service = Custom("Auth Service", path)
            user_service = Custom("User Service", path)
            billing_service = Custom("Billing Service", path)
            notification_service = Custom("Notification Service", path)
            ai_service = Custom("AI Service", path)
        with Cluster("Data Layer"):
            s3_static_assets = Custom("S3 Static Assets", path)
            postgres_primary = Custom("PostgreSQL Primary", path)
            postgres_replica = Custom("PostgreSQL Replica", path)
            redis_cache = Custom("Redis Cache", path)
            elasticsearch = Custom("Elasticsearch", path)
            s3_object_storage = Custom("S3 Object Storage", path)
        with Cluster("Infrastructure Layer"):
            cloudfront_cdn = Custom("CloudFront CDN", path)
            aws_waf = Custom("AWS WAF", path)
            aws_alb = Custom("Application Load Balancer", path)
            kafka_cluster = Custom("Kafka Cluster", path)
            secrets_manager = Custom("Secrets Manager", path)
            cloudwatch = Custom("CloudWatch", path)
            eks_cluster = Custom("Kubernetes Cluster", path)
            cicd_pipeline = Custom("CI/CD Pipeline", path)

        # Define connections
        client_browser >> Edge(label="HTTPS/Static") >> cloudfront_cdn
        cloudfront_cdn >> Edge(label="GetObject") >> s3_static_assets
        client_browser >> Edge(label="HTTPS/API") >> aws_waf
        aws_waf >> Edge(label="Filtered Traffic") >> aws_alb
        aws_alb >> Edge(label="HTTP") >> api_gateway
        api_gateway << Edge(label="REST/gRPC") << auth_service
        api_gateway << Edge(label="REST/gRPC") << user_service
        api_gateway << Edge(label="REST/gRPC") << billing_service
        api_gateway << Edge(label="REST/gRPC") << notification_service
        api_gateway << Edge(label="REST/gRPC") << ai_service
        auth_service << Edge(label="SQL Query") << postgres_primary
        auth_service >> Edge(label="GetSecret") >> secrets_manager
        user_service << Edge(label="SQL Write") << postgres_primary
        user_service >> Edge(label="SQL Read") >> postgres_replica
        user_service << Edge(label="Cache/Session") << redis_cache
        user_service << Edge(label="Search/Index") << elasticsearch
        billing_service << Edge(label="SQL Transaction") << postgres_primary
        notification_service >> Edge(label="Publish Event") >> kafka_cluster
        ai_service << Edge(label="Consume/Publish") << kafka_cluster
        ai_service << Edge(label="Read/Write Model") << s3_object_storage
        postgres_primary >> Edge(label="Streaming Replication") >> postgres_replica
        eks_cluster >> Edge(label="Hosts") >> auth_service
        eks_cluster >> Edge(label="Hosts") >> user_service
        eks_cluster >> Edge(label="Hosts") >> billing_service
        eks_cluster >> Edge(label="Hosts") >> notification_service
        eks_cluster >> Edge(label="Hosts") >> ai_service
        cicd_pipeline >> Edge(label="Deploy") >> eks_cluster
        eks_cluster >> Edge(label="Logs/Metrics") >> cloudwatch




    print("Success! Your architecture.png now contains the images.")

finally:
    # 3. Cleanup: Delete the folder and temporary icon
    if os.path.exists(ICONS_DIR):
        shutil.rmtree(ICONS_DIR)
        print("Cleanup: Temporary folder removed.")