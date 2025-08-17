from diagrams import Diagram, Cluster
from diagrams.custom import Custom
from diagrams.azure.database import SynapseAnalytics
from diagrams.azure.analytics import Databricks
from diagrams.azure.identity import ActiveDirectory
from diagrams.onprem.analytics import PowerBI
from diagrams.onprem.database import Mssql
from diagrams.onprem.client import Users

with Diagram(
    "Azure Synapse + Databricks Ingestion Workflow",
    show=False,
    direction="LR"
):
    # Users & Sources
    users = Users("Business Users")
    source_db = Mssql("On-Prem SQL Server")
    source_iot = Custom("IoT Devices / Event Hub", "./resources/iot.png")

    # Security
    aad = ActiveDirectory("Azure AD RBAC")

    # Bronze Raw Storage
    bronze = Custom("ADLS Bronze (Raw)", "./resources/datalake.png")

    # Pipeline Orchestration
    pipeline = Custom("Synapse Pipeline / ADF", "./resources/datafactory.png")

    # Databricks
    with Cluster("Databricks Processing"):
        databricks = Databricks("Cleansing & Transformation")

    # Silver and Gold Layers
    silver = Custom("ADLS Silver (Cleaned)", "./resources/datalake.png")
    gold = Custom("ADLS Gold (Aggregated)", "./resources/datalake.png")

    # Synapse Analytics Output
    synapse = SynapseAnalytics("SQL Pool (Dedicated/Serverless)")

    # Visualization
    powerbi = PowerBI("Power BI Dashboards")

    # Draw the flow
    source_db >> pipeline >> bronze
    source_iot >> pipeline
    bronze >> databricks >> silver >> databricks >> gold >> synapse >> powerbi
    aad >> [pipeline, databricks, synapse]
    users >> powerbi