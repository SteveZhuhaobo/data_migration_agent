from diagrams import Diagram, Cluster
from diagrams.aws.compute import EC2
from diagrams.aws.network import ELB
from diagrams.aws.database import RDS

with Diagram("Simple Web Service", show=True):
    lb = ELB("Load Balancer")

    with Cluster("Web Servers"):
        web_servers = [EC2("web1"),
                       EC2("web2"),
                       EC2("web3")]

    db = RDS("User Database")

    lb >> web_servers >> db
