# test_sql.py
import pandas as pd
from sqlalchemy import create_engine
import urllib

odbc_str = (
  "DRIVER={ODBC Driver 17 for SQL Server};"
  "SERVER=10.1.0.3\\SQLSTANDARD;"
  "DATABASE=dbactions;"
  "UID=analistarpt;"
  "PWD=mM=DU9lUd3C$qb@"
)
quoted = urllib.parse.quote_plus(odbc_str)
engine = create_engine(f"mssql+pyodbc:///?odbc_connect={quoted}")
SQL = """
SELECT 
    c.A00_ID,
    c.A00_FANTASIA,
    c.A00_CNPJ_CPF,
    c.A00_LAT    AS latitude,
    c.A00_LONG   AS longitude,
    v.A00_FANTASIA AS VENDEDOR,
    s.A00_FANTASIA AS SUPERVISOR,
    a.A14_DESC     AS AREA_DESC
FROM A00 c
INNER JOIN A14 a ON c.A00_ID_A14   = a.A14_ID
LEFT  JOIN A00 v ON c.A00_ID_VEND   = v.A00_ID
LEFT  JOIN A00 s ON c.A00_ID_VEND_2 = s.A00_ID
WHERE c.A00_STATUS = 1
  AND c.A00_EN_CL   = 1
  AND a.A14_DESC IS NOT NULL
  AND a.A14_DESC NOT IN (
    '999 - L80-INDUSTRIA',
    '700 - L81 - REMESSA VENDA',
    '142 - L82-PARACURU-LICITAÇÃO',
    '147 - L82-PARAIPABA-LICITAÇÃO',
    '149 - L82-SGA-LICITAÇÃO',
    '000 - L82-EXTRA ROTA'
  );
"""


df = pd.read_sql(SQL, engine)
print(df)
print("Linhas lidas:", len(df))