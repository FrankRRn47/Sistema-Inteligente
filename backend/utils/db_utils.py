"""Database helper utilities."""
from __future__ import annotations

from pathlib import Path

import pymysql
from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import OperationalError


def ensure_database_exists(connection_uri: str) -> None:
    """Create the target MySQL database if it does not exist yet."""
    if not connection_uri:
        return

    url = make_url(connection_uri)
    backend = (url.get_backend_name() or "").lower()

    if backend.startswith("sqlite"):
        db_path = url.database
        if db_path:
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        return

    if backend != "mysql":
        return

    db_name = url.database
    if not db_name:
        return

    try:
        connection = pymysql.connect(
            host=url.host or "localhost",
            user=url.username or "root",
            password=url.password or "",
            port=url.port or 3306,
            database=None,
            autocommit=True,
            cursorclass=pymysql.cursors.Cursor,
        )
    except pymysql.MySQLError as exc:
        raise RuntimeError(
            "No se pudo conectar a MySQL. Verifica que el servicio esté encendido y las credenciales sean correctas."
        ) from exc

    safe_name = db_name.replace("`", "``")
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{safe_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
    finally:
        connection.close()


def ensure_database_online(connection_uri: str, *, timeout: int = 5) -> None:
    """Validate that the configured database can be reached."""
    if not connection_uri:
        return

    url = make_url(connection_uri)
    backend = (url.get_backend_name() or "").lower()
    connect_args = {}

    if backend.startswith("mysql"):
        connect_args["connect_timeout"] = timeout

    engine = create_engine(connection_uri, pool_pre_ping=True, connect_args=connect_args)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except OperationalError as exc:
        raise RuntimeError("No se pudo establecer conexión con la base de datos configurada.") from exc
    finally:
        engine.dispose()
