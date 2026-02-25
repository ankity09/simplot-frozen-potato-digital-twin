"""
Frozen Potato Digital Twin — FastAPI Backend
~600 lines | 15 endpoints: triples, RDF parsing, telemetry, RDF models CRUD, SPARQL, health
"""

import asyncio, json, os, re, logging, html, glob as globmod
from contextlib import asynccontextmanager
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
import urllib.parse

import rdflib
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response

import psycopg2
from psycopg2.pool import ThreadedConnectionPool

from databricks.sdk import WorkspaceClient

# ─── Config ───────────────────────────────────────────────────────────────────

WAREHOUSE_ID = os.getenv("DATABRICKS_WAREHOUSE_ID", "55d3a94c50a43f96")
CATALOG = os.getenv("CATALOG", "ankit_yadav")
SCHEMA = os.getenv("SCHEMA", "frozen_potato")
TABLE = os.getenv("TABLE", "potato_sensor_bronze")
SYNCED_TABLE = os.getenv("SYNCED_TABLE_FULL_NAME", "simplot-potato-lakebase.frozen_potato.latest_sensor_triples")
TRIPLE_TABLE = os.getenv("TRIPLE_TABLE_FULL_NAME", "ankit_yadav.frozen_potato.triples")
RDF_MODELS_TABLE = os.getenv("RDF_MODELS_TABLE", "digitaltwin.rdf_models")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("digital-twin")

w = WorkspaceClient()

# ─── Lakehouse Query Execution ────────────────────────────────────────────────

def run_query(sql: str) -> list[dict]:
    """Execute SQL via Statement Execution API and return list of dicts."""
    resp = w.statement_execution.execute_statement(
        warehouse_id=WAREHOUSE_ID,
        catalog=CATALOG,
        schema=SCHEMA,
        statement=sql,
        wait_timeout="50s",
    )
    if not resp.result or not resp.result.data_array:
        return []

    manifest = resp.manifest
    columns = getattr(manifest, "columns", None) or getattr(manifest.schema, "columns", [])
    col_names = [c.name for c in columns]
    col_types = [c.type_text.upper() if c.type_text else "STRING" for c in columns]

    rows = []
    for row in resp.result.data_array:
        d = {}
        for i, val in enumerate(row):
            if val is None:
                d[col_names[i]] = None
            elif "INT" in col_types[i]:
                d[col_names[i]] = int(val)
            elif col_types[i] in ("DOUBLE", "FLOAT", "DECIMAL"):
                d[col_names[i]] = float(val)
            elif col_types[i] == "BOOLEAN":
                d[col_names[i]] = val.lower() in ("true", "1")
            else:
                d[col_names[i]] = val
        rows.append(d)
    return rows


# ─── Lakebase PostgreSQL Pool ─────────────────────────────────────────────────

_pg_pool: Optional[ThreadedConnectionPool] = None


def _get_pg_token() -> str:
    hf = w.config._header_factory
    if callable(hf):
        r = hf()
        return r.get("Authorization", "").removeprefix("Bearer ") if isinstance(r, dict) else ""
    return ""


def _init_pg_pool(force: bool = False):
    global _pg_pool
    if _pg_pool and not force:
        return
    if _pg_pool:
        try:
            _pg_pool.closeall()
        except Exception:
            pass
    host = os.getenv("PGHOST", "")
    port = int(os.getenv("PGPORT", "5432"))
    db = os.getenv("PGDATABASE", "simplot-potato-lakebase")
    user = os.getenv("PGUSER", "")
    ssl = os.getenv("PGSSLMODE", "require")
    token = _get_pg_token()
    _pg_pool = ThreadedConnectionPool(
        1, 5, host=host, port=port, dbname=db,
        user=user, password=token, sslmode=ssl,
    )
    log.info("Lakebase pool initialised  host=%s db=%s", host, db)


def _get_pg_conn():
    _init_pg_pool()
    try:
        conn = _pg_pool.getconn()
        conn.cursor().execute("SELECT 1")
        return conn
    except (psycopg2.OperationalError, psycopg2.InterfaceError):
        log.warning("Lakebase connection stale — reinitialising pool with fresh token")
        _init_pg_pool(force=True)
        return _pg_pool.getconn()


def _put_pg_conn(conn, close: bool = False):
    if _pg_pool:
        try:
            _pg_pool.putconn(conn, close=close)
        except Exception:
            pass


def _pg_rows(cur) -> list[dict]:
    cols = [d[0] for d in cur.description]
    rows = []
    for r in cur.fetchall():
        d = {}
        for i, v in enumerate(r):
            if isinstance(v, Decimal):
                d[cols[i]] = float(v)
            elif isinstance(v, (datetime, date)):
                d[cols[i]] = v.isoformat()
            else:
                d[cols[i]] = v
        rows.append(d)
    return rows


def run_pg_query(sql: str, params=None) -> list[dict]:
    conn = _get_pg_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return _pg_rows(cur)
    except (psycopg2.OperationalError, psycopg2.InterfaceError):
        _put_pg_conn(conn, close=True)
        conn = _get_pg_conn()
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return _pg_rows(cur)
    finally:
        _put_pg_conn(conn)


def write_pg(sql: str, params=None) -> Optional[dict]:
    conn = _get_pg_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            conn.commit()
            if cur.description:
                return _pg_rows(cur)[0] if cur.rowcount else None
            return {"affected": cur.rowcount}
    except (psycopg2.OperationalError, psycopg2.InterfaceError):
        _put_pg_conn(conn, close=True)
        conn = _get_pg_conn()
        with conn.cursor() as cur:
            cur.execute(sql, params)
            conn.commit()
            if cur.description:
                return _pg_rows(cur)[0] if cur.rowcount else None
            return {"affected": cur.rowcount}
    except Exception:
        conn.rollback()
        raise
    finally:
        _put_pg_conn(conn)


# ─── RDF Helpers ──────────────────────────────────────────────────────────────

def _clean_uri(value: str) -> str:
    if not value:
        return value
    v = html.unescape(value).strip("<>").strip()
    return urllib.parse.quote(v, safe=':/#?&=%@+')


def _strip_prefix(uri: str) -> str:
    if isinstance(uri, str):
        clean = uri.rstrip("/")
        parts = re.split(r'[#/]', clean)
        return parts[-1]
    return uri


def _build_graph_from_pg() -> rdflib.Graph:
    """Fetch latest triples from Lakebase and build an rdflib Graph."""
    g = rdflib.Graph()
    rows = run_pg_query(f"SELECT s, p, o FROM {SYNCED_TABLE}")
    for row in rows:
        s, p, o = row["s"], row["p"], row["o"]
        if p == "rdf:type":
            g.add((rdflib.URIRef(_clean_uri(s)), rdflib.RDF.type, rdflib.URIRef(_clean_uri(o))))
        else:
            g.add((rdflib.URIRef(_clean_uri(s)), rdflib.URIRef(_clean_uri(p)), rdflib.Literal(html.unescape(o))))
    return g


def _build_graph_from_lakehouse(timestamp: str) -> rdflib.Graph:
    """Fetch point-in-time triples from Lakehouse and build an rdflib Graph."""
    g = rdflib.Graph()
    sql = f"""
        SELECT s, p, o FROM (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY s, p ORDER BY timestamp DESC) AS rn
            FROM {TRIPLE_TABLE}
            WHERE timestamp < '{timestamp}'
        ) t WHERE rn = 1
    """
    rows = run_query(sql)
    for row in rows:
        s, p, o = row["s"], row["p"], row["o"]
        if p == "rdf:type":
            g.add((rdflib.URIRef(_clean_uri(s)), rdflib.RDF.type, rdflib.URIRef(_clean_uri(o))))
        else:
            g.add((rdflib.URIRef(_clean_uri(s)), rdflib.URIRef(_clean_uri(p)), rdflib.Literal(html.unescape(str(o)))))
    return g


def _graph_to_cytoscape(g: rdflib.Graph) -> dict:
    """Parse an rdflib Graph into Cytoscape elements JSON with hierarchy metadata."""
    elements = []
    nodes = {}
    known_parents = {}
    all_types = {}
    all_states = {}
    all_comments = {}
    labels = {}
    predicate_mapping = {}

    DT = rdflib.Namespace("http://databricks.com/digitaltwin/")
    RDFS = rdflib.namespace.RDFS

    # First pass: collect metadata
    for s, p, o in g:
        p_str = str(p)
        s_str = str(s)
        o_str = str(o)

        if p_str.endswith("subPropertyOf"):
            predicate_mapping.setdefault(s_str, {})[o_str] = True
        elif p_str.endswith("hasState"):
            all_states[s_str] = _strip_prefix(o_str)
        elif p_str.endswith("comment"):
            all_comments[s_str] = o_str
        elif p_str.endswith("label") and not p_str.endswith("subPropertyOf"):
            labels[s_str] = o_str

    def _has_predicate(given, target):
        if given == target:
            return True
        return predicate_mapping.get(given, {}).get(target, False)

    # Second pass: build elements
    for s, p, o in g:
        p_str = str(p)
        s_str = str(s)
        o_str = str(o)

        # Skip metadata triples already processed
        if p_str.endswith("subPropertyOf") or p_str.endswith("hasState") or p_str.endswith("comment"):
            continue
        if p_str.endswith("label"):
            continue
        if p == rdflib.RDF.type and (o_str.endswith("Property") or o_str.endswith("Class")):
            continue
        if p_str.endswith("range") or p_str.endswith("domain"):
            continue
        if o_str.endswith("state"):
            continue

        if _has_predicate(p_str, "http://databricks.com/digitaltwin/dependsOn"):
            elements.append({"data": {"id": f"edge-{len(elements)}", "label": _strip_prefix(p_str), "source": o_str, "target": s_str}})
        elif _has_predicate(p_str, "http://databricks.com/digitaltwin/partOf"):
            if s_str in nodes:
                elements[nodes[s_str]]["data"]["parent"] = o_str
            else:
                known_parents[s_str] = o_str
        elif p == rdflib.RDF.type:
            elem = {
                "data": {
                    "id": s_str,
                    "label": labels.get(s_str, _strip_prefix(s_str)),
                    "type": o_str,
                    "state": all_states.get(s_str, "operational"),
                    "comment": all_comments.get(s_str, ""),
                }
            }
            if s_str in known_parents:
                elem["data"]["parent"] = known_parents[s_str]
            all_types[o_str] = True
            nodes[s_str] = len(elements)
            elements.append(elem)

    # Compute hierarchy depths per type
    parent_map = {}
    for elem in elements:
        if "parent" in elem.get("data", {}):
            parent_map[elem["data"]["id"]] = elem["data"]["parent"]

    def find_hierarchy(node_id):
        path = []
        current = node_id
        while current in parent_map:
            current = parent_map[current]
            path.append(current)
        return list(reversed(path))

    type_hierarchies = {}
    for t in all_types:
        rep = next((e for e in elements if e.get("data", {}).get("type") == t), None)
        if rep:
            type_hierarchies[t] = find_hierarchy(rep["data"]["id"])

    max_depth = max((len(v) for v in type_hierarchies.values()), default=0)

    return {
        "elements": elements,
        "types": list(all_types.keys()),
        "hierarchies": type_hierarchies,
        "maxdepth": max_depth,
    }


def _graph_to_state(g: rdflib.Graph) -> dict:
    """Parse an rdflib Graph into a state map: {subject_uri: {predicate: value, ...}}."""
    components = {}
    for s, p, o in g:
        s_str = str(s)
        p_str = str(p)
        o_str = str(o)

        if p == rdflib.RDF.type:
            components.setdefault(s_str, {})
        else:
            pred_name = _strip_prefix(p_str)
            try:
                val = float(o_str)
                val = round(val, 2)
            except (ValueError, TypeError):
                val = o_str
            components.setdefault(s_str, {})[pred_name] = val
    return components


# ─── Helpers ──────────────────────────────────────────────────────────────────

_SAFE_RE = re.compile(r"^[\w\s\-.,#&'()/%]+$")

def _safe(val: str) -> str:
    if not _SAFE_RE.match(val):
        raise HTTPException(400, "Invalid filter value")
    return val


# ─── FastAPI App ──────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(application: FastAPI):
    try:
        _init_pg_pool()
    except Exception as e:
        log.warning("Lakebase pool init deferred: %s", e)
    yield

app = FastAPI(title="Frozen Potato Digital Twin", lifespan=lifespan)


# ─── Health Check ─────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    checks = {}
    try:
        w.current_user.me()
        checks["sdk"] = "ok"
    except Exception as e:
        checks["sdk"] = str(e)
    try:
        await asyncio.to_thread(run_pg_query, "SELECT 1")
        checks["lakebase"] = "ok"
    except Exception as e:
        checks["lakebase"] = str(e)
    try:
        await asyncio.to_thread(run_query, "SELECT 1")
        checks["sql_warehouse"] = "ok"
    except Exception as e:
        checks["sql_warehouse"] = str(e)
    ok = all(v == "ok" for v in checks.values())
    return {"status": "healthy" if ok else "degraded", "checks": checks}


# ═══════════════════════════════════════════════════════════════════════════════
# TRIPLES ENDPOINTS (2)
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/latest")
async def latest_triples():
    """Fetch latest triples from Lakebase, return as Turtle."""
    g = await asyncio.to_thread(_build_graph_from_pg)
    turtle = g.serialize(format="turtle")
    return Response(content=turtle, media_type="text/turtle; charset=utf-8")


@app.get("/api/pit")
async def point_in_time(timestamp: str = Query(None)):
    """Fetch point-in-time triples from Lakehouse, return as Turtle."""
    if not timestamp:
        raise HTTPException(400, "Missing required 'timestamp' query parameter")
    g = await asyncio.to_thread(_build_graph_from_lakehouse, timestamp)
    turtle = g.serialize(format="turtle")
    return Response(content=turtle, media_type="text/turtle; charset=utf-8")


# ═══════════════════════════════════════════════════════════════════════════════
# DIGITAL TWIN STRUCTURE & STATE (backend RDF parsing — replaces frontend N3)
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/digital-twin/structure")
async def digital_twin_structure():
    """Parse RDF model into Cytoscape elements JSON."""
    g = await asyncio.to_thread(_build_graph_from_pg)
    return await asyncio.to_thread(_graph_to_cytoscape, g)


@app.get("/api/digital-twin/state")
async def digital_twin_state():
    """Parse latest triples into state map JSON."""
    g = await asyncio.to_thread(_build_graph_from_pg)
    return await asyncio.to_thread(_graph_to_state, g)


@app.post("/api/sparql")
async def execute_sparql(body: dict):
    """Execute a SPARQL query server-side with rdflib."""
    query = body.get("query", "").strip()
    if not query:
        raise HTTPException(400, "Missing 'query' in request body")

    g = await asyncio.to_thread(_build_graph_from_pg)

    def _run_sparql():
        try:
            result = g.query(query)
            if result.type == "SELECT":
                cols = [str(v) for v in result.vars]
                rows = []
                for row in result:
                    rows.append({col: str(row[i]) if row[i] is not None else None for i, col in enumerate(cols)})
                return {"type": "SELECT", "columns": cols, "rows": rows, "count": len(rows)}
            elif result.type == "CONSTRUCT":
                triples = []
                for s, p, o in result:
                    triples.append({"s": str(s), "p": str(p), "o": str(o)})
                return {"type": "CONSTRUCT", "triples": triples, "count": len(triples)}
            elif result.type == "ASK":
                return {"type": "ASK", "result": bool(result)}
            else:
                return {"type": str(result.type), "message": "Query executed successfully"}
        except Exception as e:
            return {"error": str(e)}

    return await asyncio.to_thread(_run_sparql)


# ═══════════════════════════════════════════════════════════════════════════════
# TELEMETRY ENDPOINTS (2)
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/telemetry/latest")
async def telemetry_latest():
    """Latest sensor data from bronze table via Statement Execution API."""
    table_full = f"{CATALOG}.{SCHEMA}.{TABLE}"
    sql = f"""
        SELECT component_id,
               oil_temperature as sensorAReading,
               water_temperature as sensorBReading,
               belt_speed as sensorCReading,
               freezer_temperature as sensorDReading,
               timestamp
        FROM (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY component_id ORDER BY timestamp DESC) as rn
            FROM {table_full}
            WHERE timestamp >= current_timestamp() - INTERVAL 30 DAYS
        ) t WHERE rn = 1 LIMIT 50
    """
    rows = await asyncio.to_thread(run_query, sql)
    data = []
    for r in rows:
        data.append({
            "componentID": r.get("component_id", ""),
            "sensorAReading": float(r.get("sensorAReading") or 0),
            "sensorBReading": float(r.get("sensorBReading") or 0),
            "sensorCReading": float(r.get("sensorCReading") or 0),
            "sensorDReading": float(r.get("sensorDReading") or 0),
            "timestamp": r.get("timestamp", ""),
        })
    return {"data": data, "count": len(data), "table": table_full, "status": "success"}


@app.get("/api/telemetry/triples")
async def telemetry_triples():
    """Telemetry from RDF triples in Lakehouse."""
    sql = f"""
        WITH latest_sensor_triples AS (
            SELECT s as component_uri, p as sensor_property,
                   CAST(o AS DOUBLE) as sensor_value, timestamp,
                   ROW_NUMBER() OVER (PARTITION BY s, p ORDER BY timestamp DESC) as rn
            FROM {TRIPLE_TABLE}
            WHERE p IN (
                'http://example.com/potato-factory/pred/oil_temperature',
                'http://example.com/potato-factory/pred/water_temperature',
                'http://example.com/potato-factory/pred/belt_speed',
                'http://example.com/potato-factory/pred/freezer_temperature'
            )
            AND s LIKE 'http://example.com/potato-factory/component-%'
            AND o != 'None' AND o IS NOT NULL
        )
        SELECT component_uri, sensor_property, sensor_value, timestamp
        FROM latest_sensor_triples WHERE rn = 1
        ORDER BY component_uri, sensor_property
    """
    rows = await asyncio.to_thread(run_query, sql)

    components = {}
    for r in rows:
        cid = r["component_uri"].split("component-")[-1]
        if cid not in components:
            components[cid] = {
                "componentID": cid,
                "sensorAReading": 0.0, "sensorBReading": 0.0,
                "sensorCReading": 0.0, "sensorDReading": 0.0,
                "timestamp": str(r.get("timestamp", "")),
            }
        prop = r["sensor_property"]
        val = float(r["sensor_value"]) if r["sensor_value"] is not None else 0.0
        if "oil_temperature" in prop:
            components[cid]["sensorAReading"] = val
        elif "water_temperature" in prop:
            components[cid]["sensorBReading"] = val
        elif "belt_speed" in prop:
            components[cid]["sensorCReading"] = val
        elif "freezer_temperature" in prop:
            components[cid]["sensorDReading"] = val

    data = list(components.values())
    return {
        "data": data, "count": len(data), "source": "rdf_triples", "status": "success",
        "mapping": {
            "sensorAReading": "oil_temperature", "sensorBReading": "water_temperature",
            "sensorCReading": "belt_speed", "sensorDReading": "freezer_temperature",
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# RDF MODELS CRUD (6)
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/rdf-models")
async def create_rdf_model(body: dict):
    name = body.get("name", "")
    content = body.get("content", "")
    if not name or not content:
        raise HTTPException(400, "Missing required fields: name, content")
    row = await asyncio.to_thread(
        write_pg,
        f"""INSERT INTO {RDF_MODELS_TABLE}
            (name, description, category, is_template, content, creator, metadata, tags)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (name) DO NOTHING
            RETURNING id, name, description, category, is_template, creator, created_at, updated_at, metadata, tags""",
        (name, body.get("description", ""), body.get("category", "user"),
         body.get("is_template", False), content,
         body.get("creator", "anonymous"), json.dumps(body.get("metadata", {})),
         body.get("tags", [])),
    )
    if not row:
        raise HTTPException(409, "Model with this name already exists")
    return row


@app.get("/api/rdf-models")
async def list_rdf_models(
    limit: int = Query(50, le=100),
    offset: int = 0,
    category: Optional[str] = None,
    search: Optional[str] = None,
):
    where_clauses = []
    params = []
    if category:
        where_clauses.append("category = %s")
        params.append(category)
    if search:
        where_clauses.append("(name ILIKE %s OR description ILIKE %s OR content ILIKE %s)")
        pat = f"%{search}%"
        params.extend([pat, pat, pat])
    where = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    params.extend([limit, offset])

    rows = await asyncio.to_thread(
        run_pg_query,
        f"""SELECT id, name, description, category, is_template, creator,
                   created_at, updated_at, metadata, tags
            FROM {RDF_MODELS_TABLE} {where}
            ORDER BY created_at DESC LIMIT %s OFFSET %s""",
        tuple(params),
    )
    count_rows = await asyncio.to_thread(
        run_pg_query, f"SELECT COUNT(*) as total FROM {RDF_MODELS_TABLE}",
    )
    total = count_rows[0]["total"] if count_rows else 0
    return {"models": rows, "pagination": {"limit": limit, "offset": offset, "total": total}}


@app.get("/api/rdf-models/local-templates")
async def get_local_templates():
    """Scan example-ttls directory for local TTL template files."""
    # Navigate from backend/ -> app/ -> project root -> example-ttls
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ttl_dir = os.path.join(base, "example-ttls")
    templates = []
    for ttl_file in sorted(globmod.glob(os.path.join(ttl_dir, "*.ttl"))):
        filename = os.path.basename(ttl_file)
        name = filename.replace(".ttl", "").replace("_", " ").title()
        with open(ttl_file, "r", encoding="utf-8") as f:
            content = f.read()
        description = "Local TTL file template"
        for line in content.split("\n"):
            if line.strip().startswith("# ") and "prefix" not in line.lower():
                description = line.strip()[2:]
                break
        cat = "template"
        if "oil" in filename.lower() or "rig" in filename.lower():
            cat = "oil-gas"
        elif "factory" in filename.lower():
            cat = "manufacturing"
        templates.append({
            "id": f"local_{filename}", "name": name, "description": description,
            "category": cat, "is_template": True, "content": content,
            "source": "local-file", "filename": filename,
        })
    return {"templates": templates, "count": len(templates), "source": "local-files"}


@app.get("/api/rdf-models/{model_id}")
async def get_rdf_model(model_id: int):
    rows = await asyncio.to_thread(
        run_pg_query,
        f"""SELECT id, name, description, category, is_template, content, creator,
                   created_at, updated_at, metadata, tags
            FROM {RDF_MODELS_TABLE} WHERE id = %s""",
        (model_id,),
    )
    if not rows:
        raise HTTPException(404, "Model not found")
    return rows[0]


@app.put("/api/rdf-models/{model_id}")
async def update_rdf_model(model_id: int, body: dict):
    sets = ["updated_at = CURRENT_TIMESTAMP"]
    params = []
    for field in ["name", "description", "category", "content"]:
        if field in body:
            sets.append(f"{field} = %s")
            params.append(body[field])
    if "is_template" in body:
        sets.append("is_template = %s")
        params.append(body["is_template"])
    if "metadata" in body:
        sets.append("metadata = %s")
        params.append(json.dumps(body["metadata"]))
    if "tags" in body:
        sets.append("tags = %s")
        params.append(body["tags"])
    if len(sets) == 1:
        raise HTTPException(400, "No updatable fields provided")
    params.append(model_id)
    row = await asyncio.to_thread(
        write_pg,
        f"""UPDATE {RDF_MODELS_TABLE} SET {', '.join(sets)} WHERE id = %s
            RETURNING id, name, description, category, is_template, creator, created_at, updated_at, metadata, tags""",
        tuple(params),
    )
    if not row:
        raise HTTPException(404, "Model not found")
    return row


@app.delete("/api/rdf-models/{model_id}")
async def delete_rdf_model(model_id: int):
    row = await asyncio.to_thread(
        write_pg,
        f"DELETE FROM {RDF_MODELS_TABLE} WHERE id = %s RETURNING id",
        (model_id,),
    )
    if not row:
        raise HTTPException(404, "Model not found")
    return {"message": "Model deleted successfully"}


# ─── Frontend Serving ─────────────────────────────────────────────────────────

_frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "src")
app.mount("/static", StaticFiles(directory=_frontend_dir), name="static")

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    return FileResponse(os.path.join(_frontend_dir, "index.html"))
