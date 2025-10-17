
from fastapi import HTTPException

def chequear_solicitudes_activas(prestador_id: int, cursor):
    """
    Verifica si el prestador tiene solicitudes activas.
    Si tiene pedidos en estado distinto a 'finalizado' o 'cancelado',
    lanza una excepción e impide la modificación del perfil.
    """
    query = """
        SELECT COUNT(*) AS total
        FROM pedido 
        WHERE id_prestador = %s 
          AND estado NOT IN ('finalizado', 'cancelado')
    """
    cursor.execute(query, (prestador_id,))
    row = cursor.fetchone()
    count = row["total"] if row else 0

    if count > 0:
        raise HTTPException(
            status_code=400,
            detail="No se puede modificar el perfil: existen solicitudes activas asociadas al prestador."
        )

