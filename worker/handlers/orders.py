
import logging, requests
from handlers.helpers import obtener_id_real
from datetime import datetime, timezone
import urllib.parse


def _normalize_fecha(fecha, horario=None):
  """Normaliza distintos formatos de fecha/horario a un ISO datetime string.

  - fecha puede ser lista [Y, M, D], string ISO, timestamp, o None
  - horario puede ser lista [H, M]
  Retorna string ISO (ej. '2025-11-15T09:30:00+00:00') o el valor original si no puede normalizar.
  """
  try:
    if isinstance(fecha, (list, tuple)):
      y, m, d = map(int, fecha[:3])
      if isinstance(horario, (list, tuple)) and len(horario) >= 2:
        hh, mm = map(int, horario[:2])
      else:
        hh, mm = 0, 0
      dtobj = datetime(y, m, d, hh, mm, tzinfo=timezone.utc)
      return dtobj.isoformat()

    if isinstance(fecha, str):
      s = fecha
      # Manejar Z final
      if s.endswith("Z"):
        s = s[:-1] + "+00:00"

      # Intentar parsear horario si viene como string "HH:MM"
      hh = None
      mm = None
      if horario is not None:
        if isinstance(horario, (list, tuple)) and len(horario) >= 2:
          try:
            hh, mm = map(int, horario[:2])
          except Exception:
            hh = mm = None
        elif isinstance(horario, str):
          try:
            parts = horario.split(":")
            hh = int(parts[0])
            mm = int(parts[1]) if len(parts) > 1 else 0
          except Exception:
            hh = mm = None

      # Fecha en formato 'YYYY-MM-DD' -> combinar con horario si existe
      try:
        if len(s) == 10 and s.count("-") == 2:
          y, mo, d = map(int, s.split("-"))
          if hh is None:
            hh = 0
            mm = 0
          dtobj = datetime(y, mo, d, hh, mm, tzinfo=timezone.utc)
          return dtobj.isoformat()

        # Intentar parsear ISO completo (datetime con o sin timezone)
        dtobj = datetime.fromisoformat(s)
        if dtobj.tzinfo is None:
          dtobj = dtobj.replace(tzinfo=timezone.utc)
        return dtobj.isoformat()
      except Exception:
        return fecha

    if isinstance(fecha, (int, float)):
      dtobj = datetime.fromtimestamp(float(fecha), tz=timezone.utc)
      return dtobj.isoformat()

  except Exception:
    return fecha

  return fecha


def _find_pedido_internal_id(api_base, hdrs, prestador_internal, pedido_externo):
  """Buscar pedido interno por id_prestador (interno) y id_pedido (externo).
  Devuelve el campo `id` del primer resultado o None.
  """
  try:
    params = {}
    if prestador_internal is not None:
      params["id_prestador"] = prestador_internal
    if pedido_externo is not None:
      params["id_pedido"] = pedido_externo
    query = urllib.parse.urlencode(params)
    url = f"{api_base}/pedidos"
    if query:
      url = f"{url}?{query}"
    resp = requests.get(url, headers=hdrs, timeout=5)
    if resp.status_code != 200:
      logging.warning(f"⚠️ Búsqueda de pedido falló ({resp.status_code}): {resp.text}")
      return None
    items = resp.json()
    if isinstance(items, list) and len(items) > 0:
      return items[0].get("id")
    return None
  except requests.RequestException as e:
    logging.error(f"💥 Error buscando pedido: {e}")
    return None

def handle(event_name, payload, api_base_url, headers):
  # COTIZACION CREADA --> testear
  if event_name == "emitida":
    logging.info("📦 Nueva solicitud de cotización emitida")
    payload_data = payload.get("payload", {})

    solicitudes = payload_data.get("solicitudes", [])
    if not solicitudes:
        logging.warning("⚠️ No se encontraron solicitudes en el payload, evento ignorado.")
        return

    total_creados = 0

    for solicitud in solicitudes:
      solicitud_id = solicitud.get("solicitudId")
      
      descripcion = solicitud.get("descripcion")
      es_critico = solicitud.get("esCritica", False)
      # Fecha puede venir como [YYYY,MM,DD] o como timestamp/ISO string
      raw_fecha = solicitud.get("fecha")
      raw_horario = solicitud.get("horario")
      fecha_normalizada_base = _normalize_fecha(raw_fecha, raw_horario)

      id_usuario_real = solicitud.get("usuarioId")
      id_usuario = obtener_id_real(id_usuario_real, "usuarios", "id_usuario", api_base_url, headers)
      direccion_dict = solicitud.get("direccion")
      if direccion_dict:
        parts = []
        prov = direccion_dict.get('provincia')
        ciudad = direccion_dict.get('ciudad')
        calle = direccion_dict.get('calle')
        numero = direccion_dict.get('numero')
        piso = direccion_dict.get('piso')
        depto = direccion_dict.get('depto') or direccion_dict.get('departamento')
        cp = direccion_dict.get('codigoPostal') or direccion_dict.get('codigo_postal')
        if prov:
          parts.append(prov)
        if ciudad:
          parts.append(ciudad)
        if calle and numero:
          parts.append(f"{calle} {numero}")
        elif calle:
          parts.append(calle)
        if piso:
          parts.append(f"Piso {piso}")
        if depto:
          parts.append(f"Depto {depto}")
        if cp:
          parts.append(f"CP {cp}")
        direccion = ", ".join(parts)
      else:
        direccion = ""

      # Recorrer los prestadores en top3
      for prestador in solicitud.get("top3", []):
        # Si el prestador trae su propio horario/fecha, priorizarlo
        prest_fecha_raw = prestador.get("fecha") or raw_fecha
        prest_horario_raw = prestador.get("horario") or raw_horario
        fecha_para_prestador = _normalize_fecha(prest_fecha_raw, prest_horario_raw) if (prest_fecha_raw or prest_horario_raw) else fecha_normalizada_base
        id_prestador = obtener_id_real(prestador.get("prestadorId"), "prestadores", "id_prestador", api_base_url, headers)
        body = {
          "id_pedido": solicitud_id,
          "descripcion": descripcion or f"Solicitud {solicitud_id}",
          "estado": "pendiente",
          "es_critico": es_critico,
          "fecha": fecha_para_prestador,
          "id_habilidad": prestador.get("habilidadId"),
          "id_prestador": id_prestador,
          "id_usuario": id_usuario,
          "direccion": direccion,
          "tarifa": None
        }

        logging.info(f"📝 Creando pedido para prestador {prestador.get('prestadorNombre')} con body: {body}")

        try:
          response = requests.post(
            f"{api_base_url}/pedidos/",
            json=body,
            headers=headers,
            timeout=5
          )

          if response.status_code == 201:
            total_creados += 1
            logging.info(f"✅ Pedido creado correctamente para prestador {prestador.get('prestadorId')}")
          else:
            logging.warning(f"⚠️ Error creando pedido ({response.status_code}): {response.text}")

        except requests.Timeout:
          logging.error(f"⏰ Timeout al crear pedido para prestador {prestador.get('prestadorId')}")
        except requests.RequestException as e:
          logging.error(f"💥 Error de request al crear pedido: {e}")

    logging.info(f"📊 Total de pedidos creados: {total_creados}")

  # COTIZACION ACEPTADA
  elif event_name == "aceptada":
      logging.info("📦 Nueva solicitud de cotización aceptada")
      logging.info(f"Payload recibido: {payload}")
      data = payload.get("payload", {})
      if not data:
          logging.warning("⚠️ No se encontró payload con datos de pago, evento ignorado.")
          return

      pedido_externo = data.get("solicitud_id")
      prestador_ext = data.get("prestador_id")

      prestador_int = None
      if prestador_ext is not None:
          try:
              prestador_int = obtener_id_real(prestador_ext, "prestadores", "id_prestador", api_base_url, headers)
          except Exception:
              prestador_int = None

      id_pedido_internal = _find_pedido_internal_id(api_base_url, headers, prestador_int, pedido_externo)
      if id_pedido_internal is None:
          logging.warning(f"⚠️ No se encontró pedido interno para solicitud {pedido_externo} y prestador {prestador_ext}")
          return

      # Normalización del payload
      body = {
          "estado": "aprobado_por_usuario",
          "tarifa": data.get("monto")
      }
      logging.info(f"🔄 Payload normalizado: {body}")

      # persistir en la tabla pedidos
      try:
          response = requests.patch(
              f"{api_base_url}/pedidos/{id_pedido_internal}",
              json=body,
              timeout=5,
              headers=headers
          )
          logging.info(f"Respuesta del API al actualizar el pedido: {response.status_code} - {response.text}")
          if response.status_code == 200:
              logging.info("✅ Cotización aceptada")
      except requests.Timeout:
          logging.error("⏰ Timeout al crear pedido")
      except requests.RequestException as e:
          logging.error(f"💥 Error al crear pedido: {e}")

  # COTIZACION RECHAZADA (igual que cancelación de pedidos)
  elif event_name == "rechazada":
    logging.info("📦 Nueva solicitud de pedido cancelado")
    logging.info(f"Payload recibido: {payload}")
    data = payload.get("payload", {})
    if not data:
      logging.warning("⚠️ No se encontró payload con datos de pago, evento ignorado.")
      return

    pedido_externo = data.get("solicitud_id")
    prestador_ext = data.get("prestador_id")
    prestador_int = None
    if prestador_ext is not None:
      try:
        prestador_int = obtener_id_real(prestador_ext, "prestadores", "id_prestador", api_base_url, headers)
      except Exception:
        prestador_int = None

    id_pedido_internal = _find_pedido_internal_id(api_base_url, headers, prestador_int, pedido_externo)
    if id_pedido_internal is None:
      logging.warning(f"⚠️ No se encontró pedido interno para solicitud {pedido_externo} y prestador {prestador_ext}")
      return

    try:
      response = requests.delete(
        f"{api_base_url}/pedidos/{id_pedido_internal}",
        timeout=5,
        headers=headers
      )
      logging.info(f"Respuesta del API al cancelar el pedido: {response.status_code} - {response.text}")
    except requests.Timeout:
      logging.error("⏰ Timeout al cancelar pedido")
    except requests.RequestException as e:
      logging.error(f"💥 Error al cancelar pedido: {e}")
  
  elif event_name == "cancelada":
    logging.info("📦 Evento de cotización cancelada - marcar pedidos como cancelado")
    logging.info(f"Payload recibido: {payload}")
    data = payload.get("payload", {})
    if not data:
      logging.warning("⚠️ No se encontró payload con datos, evento ignorado.")
      return

    # Aceptamos varias claves que pueden nombrar al id externo
    solicitud_id = data.get("solicitud_id")
    if not solicitud_id:
      logging.warning("⚠️ No se encontró 'solicitud_id' en el payload, evento ignorado.")
      return

    try:
      # Obtener todos los pedidos que coincidan con el id_pedido externo
      url = f"{api_base_url}/pedidos"
      resp = requests.get(url, headers=headers, params={"id_pedido": solicitud_id}, timeout=5)
      if resp.status_code != 200:
        logging.warning(f"⚠️ Falló la búsqueda de pedidos para solicitud {solicitud_id} ({resp.status_code}): {resp.text}")
        return

      items = resp.json()
      if not isinstance(items, list) or len(items) == 0:
        logging.info(f"ℹ️ No se encontraron pedidos para solicitud {solicitud_id}.")
        return

      # Actualizar cada pedido a estado 'cancelado'
      for item in items:
        pedido_internal_id = item.get("id")
        if not pedido_internal_id:
          continue
        try:
          patch_resp = requests.patch(
            f"{api_base_url}/pedidos/{pedido_internal_id}",
            json={"estado": "cancelado"},
            timeout=5,
            headers=headers
          )
          logging.info(f"Respuesta al actualizar pedido {pedido_internal_id}: {patch_resp.status_code} - {patch_resp.text}")
          if patch_resp.status_code == 200:
            logging.info(f"✅ Pedido interno {pedido_internal_id} marcado como 'cancelado'")
        except requests.Timeout:
          logging.error(f"⏰ Timeout al actualizar pedido {pedido_internal_id}")
        except requests.RequestException as e:
          logging.error(f"💥 Error al actualizar pedido {pedido_internal_id}: {e}")

    except requests.RequestException as e:
      logging.error(f"💥 Error buscando pedidos para solicitud {solicitud_id}: {e}")
