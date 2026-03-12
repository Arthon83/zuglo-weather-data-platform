import os
from databricks import sql
from dotenv import load_dotenv



def get_connection():
    server_hostname = os.getenv("DATABRICKS_SERVER_HOSTNAME")
    http_path = os.getenv("DATABRICKS_HTTP_PATH")
    access_token = os.getenv("DATABRICKS_TOKEN")

    missing = [
        name for name, value in {
            "DATABRICKS_SERVER_HOSTNAME": server_hostname,
            "DATABRICKS_HTTP_PATH": http_path,
            "DATABRICKS_TOKEN": access_token,
        }.items() if not value
    ]

    if missing:
        raise ValueError(
            f"Hiányzó környezeti változók: {', '.join(missing)}"
        )

    return sql.connect(
        server_hostname=server_hostname,
        http_path=http_path,
        access_token=access_token,
    )