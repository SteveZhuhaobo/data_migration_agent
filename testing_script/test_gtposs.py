#!/usr/bin/env python3
"""
Simple AWS‑only data‑pipeline diagram that includes a Databricks node
(using a custom image).
"""

# ------------------------------------------------------------------
# Imports – note the *custom* node for Databricks
# ------------------------------------------------------------------
from diagrams import Diagram
from diagrams.aws.storage import S3
from diagrams.aws.compute import EC2
from diagrams.aws.analytics import Redshift
from diagrams.custom import Custom   # for Databricks icon

# ------------------------------------------------------------------
# Diagram definition
# ------------------------------------------------------------------
with Diagram(
    name="AWS Data Pipeline",
    filename="aws_databricks_pipeline",   # → will create .png, .svg, …
    direction="LR",                       # Top‑to‑Bottom layout (LR, RL, BT also work)
    outformat="png",
    show=False,                           # set True if you want the image to open automatically
) as diag:

    # ------------------------------------------------------------------
    # Nodes (icons)
    # ------------------------------------------------------------------
    raw = S3("Raw data\n(S3 bucket)")
    vm  = EC2("ETL runner\n(EC2 instance)")

    # Databricks – replace the URL with any image you like
    db = Custom(
        "Databricks\nCluster",
        "./databricks.png"   # local path – see step 3 to download the file
    )

    dw  = Redshift("Redshift\nWarehouse")

    # ------------------------------------------------------------------
    # Edges (arrows)
    # ------------------------------------------------------------------
    raw >> vm >> db >> dw