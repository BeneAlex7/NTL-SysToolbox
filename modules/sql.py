import mysql.connector
from rich.console import Console
from rich.table import Table
from rich import box
import io
import getpass
import time


def evaluate_status(latency_ms, threads):

    if latency_ms > 2000 or threads > 100:
        return "CRITICAL"
    elif latency_ms > 1000 or threads > 50:
        return "WARNING"
    else:
        return "OK"


def format_table(data, target, status):

    console = Console(file=io.StringIO(), force_terminal=True, width=120)

    table = Table(
        title=f"SQL DATABASE STATUS: {target} [{status}]",
        box=box.ROUNDED,
        header_style="bold cyan"
    )

    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="center")

    for key, value in data.items():
        table.add_row(str(key), str(value))

    console.print(table)
    console.print("\n")

    return console.file.getvalue()


def run(config):

    conn = None
    cursor = None

    try:

        infra = config.get("infrastructure", {})
        wms = infra.get("wms", {})

        db_ip = wms.get("db_ip")
        db_name = wms.get("db_name")

        if not db_ip:
            raise Exception("Database IP not defined in config")

        print(f"\n[SQL] Target database: {db_name} ({db_ip})")

        sql_conf = config.get("sql", {})

        user = sql_conf.get("user")
        password = sql_conf.get("password")

        if not user:
            user = input("SQL user: ")

        if not password:
            password = getpass.getpass("SQL password: ")

        # Measure latency
        start_time = time.time()

        conn = mysql.connector.connect(
            host=db_ip,
            user=user,
            password=password,
            database=db_name,
            connection_timeout=5
        )

        latency_ms = round((time.time() - start_time) * 1000, 2)

        cursor = conn.cursor()

        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]

        cursor.execute("SHOW GLOBAL STATUS LIKE 'Uptime'")
        uptime = cursor.fetchone()[1]

        cursor.execute("SHOW STATUS LIKE 'Threads_connected'")
        threads = int(cursor.fetchone()[1])

        cursor.execute("""
            SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 2)
            FROM information_schema.tables
            WHERE table_schema = %s
        """, (db_name,))
        db_size = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = %s
        """, (db_name,))
        tables_count = cursor.fetchone()[0]

        status = evaluate_status(latency_ms, threads)

        data = {
            "database": db_name,
            "mysql_version": version,
            "latency_ms": latency_ms,
            "uptime_seconds": uptime,
            "active_connections": threads,
            "database_size_MB": db_size,
            "tables_count": tables_count
        }

        return {
            "module": "sql_monitor",
            "status": status,
            "code": 0 if status == "OK" else 1,
            "target": db_ip,
            "data": data,
            "message": format_table(data, db_ip, status)
        }

    except Exception as e:

        return {
            "module": "sql_monitor",
            "status": "ERROR",
            "code": 1,
            "target": config.get("infrastructure", {}).get("wms", {}).get("db_ip", "unknown"),
            "data": {},
            "message": f"SQL monitoring error: {str(e)}"
        }

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()