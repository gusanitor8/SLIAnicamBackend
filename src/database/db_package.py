from config.database import Session
from dataModels.paquete import PaqueteBase
from dataModels.consolidado import ConsolidadoBase
from models.paquete_table import Paquete
from models.consolidado_table import Consolidado
from models.consolidacion_table import Consolidacion
from models.seguimiento_paquete_table import SeguimientoPaquete
from sqlalchemy.exc import IntegrityError, DataError, OperationalError
from typing import List


def precarga_paquetes(paquetes: List[PaqueteBase], consolidado: ConsolidadoBase, user: int):
    try:
        session = Session()

        # Creacion e insercion de un nuevo consolidado
        consolidado_obj = Consolidado(
            # id_consolidado autogenerado
            descripcion=consolidado.descripcion,
            transportista=consolidado.transportista
            # fecha_consolidacion autogenerada
        )
        session.add(consolidado_obj)
        # obtencion de IDs sin hacer commit
        session.flush()

        # Creacion e insercion de paquetes
        paquetes_objs = []
        for paquete in paquetes:
            paquete_obj = Paquete(
                # id_paquete autogenerado
                factura=paquete.factura,
                fecha_orden=paquete.fecha_orden,
                contenido=paquete.contenido,
                descripcion=paquete.descripcion,
                alto=paquete.alto,
                ancho=paquete.ancho,
                largo=paquete.largo,
                peso_libras=paquete.peso_libras,
                peso_volumetrico=paquete.peso_volumetrico,
                valor_producto_dolar=paquete.valor_producto_dolar,
                unidades=paquete.unidades,
                direccion_casillero=paquete.direccion_casillero,
                empresa_remitente=paquete.empresa_remitente,
                cliente_nombre=paquete.cliente_nombre,
                cliente_telefono=paquete.cliente_telefono,
                cliente_email=paquete.cliente_email,
                cliente_direccion=paquete.cliente_direccion
            )
            session.add(paquete_obj)

            # obtencion de IDs sin hacer commit
            session.flush()
            paquetes_objs.append(paquete_obj)

        # Cracion e insercion de consolidaciones
        for package in paquetes_objs:
            consolidacion_obj = Consolidacion(
                consolidado_id=consolidado_obj.id_consolidado,
                paquete_id=package.id_paquete
            )
            session.add(consolidacion_obj)

            # Creacion e insercion de registro de seguimiento para cada paquete
            seguimiento_obj = SeguimientoPaquete(
                estado_actual='en transito',
                motivo_cambio='Precarga de paquete',
                paquete_id=package.id_paquete,
                usuario_id=user
            )
            session.add(seguimiento_obj)

        session.commit()

    except IntegrityError as e:
        session.rollback()
        raise ValueError(
            "Error de integridad: posible registro duplicado o violacion de restricciones. " + str(e)) from e

    except DataError as e:
        session.rollback()
        raise ValueError("Error de datos: campos nulos, incompletos o tipo de datos inadecuado." + str(e)) from e

    except OperationalError as e:
        session.rollback()
        raise Exception("Error operacional en la base de datos.") from e

    except Exception as e:
        session.rollback()
        raise Exception(f"Error inesperado: {str(e)}") from e

    finally:
        session.close()


def get_consolidado(consolidado_id: int):
    try:
        session = Session()
        consolidado = session.query(Consolidado).filter(Consolidado.id_consolidado == consolidado_id).first()

        if consolidado:
            consolidado = consolidado.to_dict()
            consolidado['fecha_consolidacion'] = consolidado['fecha_consolidacion'].isoformat()
            return consolidado
        return {}
    finally:
        session.close()


def get_paquete(paquete_id: int):
    try:
        session = Session()
        paquetes = session.query(Paquete).filter(Paquete.id_paquete == paquete_id).first()

        if paquetes:
            paquetes = paquetes.to_dict()
            paquetes['fecha_orden'] = paquetes['fecha_orden'].isoformat()
            return paquetes
        return {}
    finally:
        session.close()


def invoice_search(invoice: str):
    try:
        session = Session()
        paquetes = session.query(Paquete).filter(Paquete.factura.like(f'%{invoice}%')).limit(10).all()

        if paquetes:
            paquetes = [paquete.to_dict() for paquete in paquetes]
            for paquete in paquetes:
                paquete['fecha_orden'] = paquete['fecha_orden'].isoformat()
            return paquetes
        return {}
    finally:
        session.close()
