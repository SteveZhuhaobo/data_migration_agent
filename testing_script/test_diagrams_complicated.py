from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import ECS, Lambda
from diagrams.aws.database import RDS, Dynamodb
from diagrams.aws.network import ELB, CloudFront, Route53
from diagrams.aws.storage import S3
from diagrams.aws.integration import SQS, SNS
from diagrams.aws.security import IAM
from diagrams.aws.analytics import Kinesis
from diagrams.onprem.client import Users
from diagrams.onprem.monitoring import Grafana
from diagrams.programming.flowchart import Decision

# Complex multi-tier architecture example
with Diagram("Complex E-commerce Platform", show=False, direction="TB", outformat="svg"):
    users = Users("Users")
    dns = Route53("DNS")
    cdn = CloudFront("CDN")
    
    with Cluster("Load Balancing Layer"):
        lb = ELB("Load Balancer")
    
    with Cluster("Web Tier"):
        web_services = [
            ECS("User Service"),
            ECS("Product Service"), 
            ECS("Order Service")
        ]
    
    with Cluster("API Gateway Layer"):
        api_decision = Decision("Rate Limiting")
    
    with Cluster("Microservices"):
        with Cluster("User Management"):
            user_api = Lambda("User API")
            user_db = RDS("User DB")
        
        with Cluster("Product Catalog"):
            product_api = Lambda("Product API")
            product_cache = Dynamodb("Product Cache")
            product_images = S3("Images")
        
        with Cluster("Order Processing"):
            order_api = Lambda("Order API")
            order_queue = SQS("Order Queue")
            payment_service = Lambda("Payment")
            inventory_service = Lambda("Inventory")
    
    with Cluster("Data & Analytics"):
        data_stream = Kinesis("Event Stream")
        analytics_db = RDS("Analytics DB")
    
    with Cluster("Notification System"):
        notifications = SNS("Notifications")
        email_service = Lambda("Email Service")
    
    with Cluster("Monitoring"):
        monitoring = Grafana("Monitoring")
        security = IAM("Security")
    
    # Define relationships
    users >> dns >> cdn >> lb
    lb >> web_services
    web_services >> api_decision
    
    # Connect to microservices
    api_decision >> user_api >> user_db
    api_decision >> product_api >> product_cache
    product_api >> product_images
    api_decision >> order_api >> order_queue
    
    order_queue >> [payment_service, inventory_service]
    
    # Data flow
    [user_api, product_api, order_api] >> data_stream >> analytics_db
    
    # Notifications
    [payment_service, inventory_service] >> notifications >> email_service
    
    # Monitoring connections
    monitoring >> Edge(style="dashed") >> web_services
    security >> Edge(style="dashed", color="red") >> [user_api, product_api, order_api]

# Example with custom styling and complex flows
with Diagram("Data Pipeline Architecture", show=False, direction="LR"):
    with Cluster("Data Sources"):
        sources = [
            S3("Raw Data"),
            RDS("Transactional DB"),
            Kinesis("Real-time Stream")
        ]
    
    with Cluster("Processing Layer"):
        etl = Lambda("ETL Process")
        batch_processor = ECS("Batch Processor")
        stream_processor = Lambda("Stream Processor")
    
    with Cluster("Storage Layer"):
        data_lake = S3("Data Lake")
        warehouse = RDS("Data Warehouse")
        cache = Dynamodb("Cache Layer")
    
    with Cluster("Analytics & ML"):
        analytics = Lambda("Analytics Engine")
        ml_service = Lambda("ML Models")
        reporting = Grafana("Dashboards")
    
    # Complex data flows
    sources[0] >> Edge(label="batch", style="bold") >> etl >> batch_processor
    sources[1] >> Edge(label="CDC", color="blue") >> etl
    sources[2] >> Edge(label="real-time", color="green") >> stream_processor
    
    batch_processor >> data_lake
    stream_processor >> [cache, data_lake]
    etl >> warehouse
    
    [data_lake, warehouse, cache] >> analytics >> reporting
    data_lake >> ml_service >> cache