def _fila_a_dict(cursor, fila):

    if fila is None:

        return None

    columnas = [columna[0] for columna in cursor.description]
    return dict(zip(columnas, fila))


def obtener_campana_activa(conn):

    cursor = conn.execute(
        """
        SELECT id,nombre,fecha_inicio,fecha_fin,activa
        FROM campanas
        WHERE activa=1
        ORDER BY id DESC
        LIMIT 1
        """
    )
    return _fila_a_dict(cursor, cursor.fetchone())


def validar_unica_campana_activa(conn):

    total = conn.execute(
        """
        SELECT COUNT(*)
        FROM campanas
        WHERE activa=1
        """
    ).fetchone()[0]
    return int(total) <= 1


def activar_campana(conn, campana_id):

    campana_id = int(campana_id)

    with conn:

        existe = conn.execute(
            """
            SELECT 1
            FROM campanas
            WHERE id=?
            """,
            (campana_id,),
        ).fetchone()

        if existe is None:

            raise ValueError(f"No existe la campana con id {campana_id}")

        conn.execute("UPDATE campanas SET activa=0")
        conn.execute(
            """
            UPDATE campanas
            SET activa=1
            WHERE id=?
            """,
            (campana_id,),
        )

        if not validar_unica_campana_activa(conn):

            raise RuntimeError("Hay mas de una campana activa")


def desactivar_campanas(conn):

    with conn:

        conn.execute("UPDATE campanas SET activa=0")

        if not validar_unica_campana_activa(conn):

            raise RuntimeError("Hay mas de una campana activa")
