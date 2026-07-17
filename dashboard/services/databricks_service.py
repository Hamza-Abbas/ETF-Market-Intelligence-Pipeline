import pandas as pd
import streamlit as st
from databricks import sql


@st.cache_data(ttl=300, show_spinner=False)
def run_query(query: str) -> pd.DataFrame:
    """
    Run a read-only SQL query against Databricks
    and return the result as a Pandas DataFrame.
    """

    credentials = st.secrets["databricks"]

    with sql.connect(
        server_hostname=credentials["server_hostname"],
        http_path=credentials["http_path"],
        access_token=credentials["access_token"],
        catalog=credentials["catalog"],
        schema=credentials["schema"],
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)

            rows = cursor.fetchall()

            if cursor.description is None:
                return pd.DataFrame()

            column_names = [
                column[0]
                for column in cursor.description
            ]

    return pd.DataFrame(rows, columns=column_names)