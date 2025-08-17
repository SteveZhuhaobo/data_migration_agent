# Import core classes from diagrams
from diagrams import Diagram, Cluster
from diagrams.aws.compute import EC2
from diagrams.aws.database import RDS
from diagrams.aws.network import ELB
from diagrams.aws.network import Route53
from diagrams.aws.network import CloudFront

# Create a diagram context
with Diagram("Simple Web Service Architecture", show=True, direction="LR"):
    # DNS and CDN layer
    dns = Route53("DNS")
    cdn = CloudFront("CDN")

    # Load balancer
    lb = ELB("Load Balancer")

    # Application servers in a cluster
    with Cluster("Application Layer"):
        app_servers = [EC2("App Server 1"),
                       EC2("App Server 2"),
                       EC2("App Server 3")]

    # Database layer
    db = RDS("User Database")

    # Connections
    dns >> cdn >> lb >> app_servers
    app_servers >> db