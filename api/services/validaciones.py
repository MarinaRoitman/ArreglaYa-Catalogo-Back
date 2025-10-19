from fastapi import HTTPException

def chequear_solicitudes_activas(prestador_id: int, cursor):
    """
    Verifica si el prestador tiene CUALQUIER solicitud activa.
    Si tiene pedidos en estado distinto a 'finalizado' o 'cancelado',
    lanza una excepción. Útil para acciones generales como desactivar un perfil.
    """
    query = """
        SELECT COUNT(*) AS total
        FROM pedido 
        WHERE id_prestador = %s 
          AND estado NOT IN ('finalizado', 'cancelado')
    """
    cursor.execute(query, (prestador_id,))
    row = cursor.fetchone()
    count = row["total"] if isinstance(row, dict) and row["total"] else 0

    if count > 0:
        raise HTTPException(
            status_code=400,
            detail="No se puede modificar el perfil: existen solicitudes activas asociadas al prestador."
        )

def chequear_pedidos_activos_por_zona(prestador_id: int, id_zona: int, cursor):
    """
    Verifica si el prestador tiene pedidos activos EN UNA ZONA ESPECÍFICA.
    Si es así, impide que se quite esa zona del prestador.
    """
    query = """
        SELECT COUNT(*) AS total
        FROM pedido
        WHERE id_prestador = %s
          AND id_zona = %s
          AND estado NOT IN ('finalizado', 'cancelado')
    """
    cursor.execute(query, (prestador_id, id_zona))
    row = cursor.fetchone()
    count = row["total"] if isinstance(row, dict) and row["total"] else 0

    if count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede quitar la zona {id_zona}: existen pedidos activos asociados a ella."
        )

def chequear_pedidos_activos_por_habilidad(prestador_id: int, id_habilidad: int, cursor):
    """
    Verifica si el prestador tiene pedidos activos PARA UNA HABILIDAD ESPECÍFICA.
    Si es así, impide que se quite esa habilidad del prestador.
    """
    query = """
        SELECT COUNT(*) AS total
        FROM pedido
        WHERE id_prestador = %s
          AND id_habilidad = %s
          AND estado NOT IN ('finalizado', 'cancelado')
    """
    cursor.execute(query, (prestador_id, id_habilidad))
    row = cursor.fetchone()
    count = row["total"] if isinstance(row, dict) and row["total"] else 0
    
    if count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede quitar la habilidad {id_habilidad}: existen pedidos activos asociados a ella."
        )