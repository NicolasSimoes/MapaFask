from flask import Flask, Response
from sqlalchemy import create_engine
import pandas as pd
import folium
import urllib

app = Flask(__name__)

odbc_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=10.1.0.3\\SQLSTANDARD;"
    "DATABASE=dbactions;"
    "UID=analistarpt;"
    "PWD=mM=DU9lUd3C$qb@"
)
conn_str = "mssql+pyodbc:///?odbc_connect=" + urllib.parse.quote_plus(odbc_str)
engine = create_engine(conn_str)

SQL = """
SELECT 
    c.A00_ID,
    c.A00_FANTASIA,
    c.A00_LAT        AS latitude,
    c.A00_LONG       AS longitude,
    a.A14_DESC       AS AREA_DESC
FROM A00 c
INNER JOIN A14 a ON c.A00_ID_A14 = a.A14_ID
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

@app.route("/")
def index():
    try:
        df = pd.read_sql(SQL, engine)
    except Exception as e:
        return Response(f"<pre style='color:red'>ERRO AO LER DO BANCO:\n{e}</pre>", mimetype="text/html")

    centro = [df.latitude.mean(), df.longitude.mean()]
    m = folium.Map(location=centro, zoom_start=6, width="100%", height="100%", tiles="CartoDB positron")

    for _, r in df.iterrows():
        folium.Marker(
            [r.latitude, r.longitude],
            popup=(f"<b>ID:</b> {r.A00_ID}<br><b>Cliente:</b> {r.A00_FANTASIA}<br><b>Área:</b> {r.AREA_DESC}"),
        ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    html = m.get_root().render()

    def make_filter_group(group_id, label, values):
        checkbox_items = "".join(f"<label><input type='checkbox' value='{v}'> {v}</label>" for v in sorted(values))
        return f"""
        <div class="filter-group" id="{group_id}">
            <label>{label}</label>
            <input type="text" class="filter-search" placeholder="Buscar {label.lower()}...">
            <label><input type="checkbox" class="check-all"> Selecionar todos</label>
            <div class="scrollbox">{checkbox_items}</div>
        </div>
        """

    area_group  = make_filter_group("area-group", "Área", df["AREA_DESC"].unique())
    id_group    = make_filter_group("id-group", "ID", df["A00_ID"].astype(str).unique())
    name_group  = make_filter_group("name-group", "Cliente", df["A00_FANTASIA"].unique())

    overlay = f"""
<style>
  #filter-toggle {{
    position: fixed;
    top: 10px;
    left: 10px;
    background: white;
    border: none;
    padding: 6px 12px;
    z-index: 1101;
    border-radius: 4px;
    cursor: pointer;
    font-weight: bold;
  }}
  #filter-popup {{
    display: none;
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: #0066cc;
    color: white;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 0 20px rgba(0,0,0,0.4);
    z-index: 1100;
    width: 320px;
    max-height: 90vh;
    overflow-y: auto;
    font-family: sans-serif;
  }}
  #filter-popup.active {{ display: block; }}
  .filter-popup-close {{
    float: right;
    background: white;
    color: white;
    border: none;
    padding: 2px 4px;                               
    border-radius: 10px;
    cursor: pointer;
  }}
  .filter-group {{
    margin-bottom: 10px;
  }}
  .filter-group label {{
    font-weight: bold;
    font-size: 12px;
    display: block;
    margin-top: 8px;
  }}
  .filter-search {{
    width: 100%;
    padding: 4px;
    margin-bottom: 4px;
    border-radius: 4px;
    border: none;
    font-size: 12px;
  }}
  .scrollbox {{
    background: white;
    padding: 4px;
    border-radius: 4px;
    max-height: 60px;
    overflow-y: auto;
    color: black;
    font-size: 12px;
  }}
  .scrollbox label {{
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 1px 0;
    font-size: 12px;
    line-height: 1.1;
  }}
  .btn-group {{
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
    margin-top: 10px;
  }}
  .panel-filtro button {{
    padding: 5px 10px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 12px;
  }}
  .btn-buscar {{ background-color: #ffffff; color: #0066cc; font-weight: bold; }}
  .btn-clear  {{ background-color: #f0f0f0; color: #000; }}
  .btn-desmarcar {{ background-color: #ff6666; color: white; }}
  .btn-toggle {{ background-color: #e0e0e0; color: #000; }}

  #counter {{
    position: fixed;
    top: 10px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(0,0,0,0.7);
    color: white;
    padding: 6px 12px;
    border-radius: 6px;
    font-family: sans-serif;
    font-size: 14px;
    z-index: 1100;
  }}
</style>

<button id="filter-toggle">🔍 Filtros</button>

<div id="counter">Registros visíveis: <span id="marker-count">0</span></div>

<div id="filter-popup">
  <button class="filter-popup-close" onclick="document.getElementById('filter-popup').classList.remove('active')">❌</button>
  {area_group}
  {id_group}
  {name_group}
  <button id="btn-search" class="btn-buscar">Buscar</button>
  <div class="btn-group">
    <button id="btn-clear" class="btn-clear">Limpar</button>
    <button id="btn-deselect" class="btn-desmarcar">Desmarcar</button>
    <button id="btn-toggle" class="btn-toggle">Toggle Filtro</button>
  </div>
</div>

<script>
  document.getElementById("filter-toggle").onclick = function() {{
    document.getElementById("filter-popup").classList.add("active");
  }};
</script>
"""

    html = html.replace("</body>", overlay + '<script src="/static/filters.js"></script></body>')
    return Response(html, mimetype="text/html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
