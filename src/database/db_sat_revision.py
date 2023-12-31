from config.database import Session
from dataModels.revision_sat import RevisionSatBase
from models.revision_sat_table import RevisionSat
from models.paquete_table import Paquete
from models.impuesto_table import Impuesto
from models.gasto_table import Gasto
from models.seguimiento_paquete_table import SeguimientoPaquete
from sqlalchemy.exc import IntegrityError, DataError, OperationalError, NoResultFound

def registrar_revision(revision: RevisionSatBase, paquete_id: int, user: int):
    
    try:
        
        session = Session()
        # Validar que no sean nulos los nuevos valores
        if revision.nuevo_valor_dai or revision.nuevo_valor_paquete:
            try:
                paquete = session.query(Paquete).filter(Paquete.id_paquete == paquete_id).one()
            except NoResultFound:
                raise ValueError("Paquete no encontrado con el ID proporcionado.")

            try:
                impuesto = session.query(Impuesto).filter(Impuesto.paquete_id == paquete_id).one()
            except NoResultFound:
                raise ValueError("Impuesto no encontrado para el paquete proporcionado.")

            # Actualizar los valores del paquete e impuesto si es necesario
            if revision.nuevo_valor_paquete:
                paquete.valor_producto_dolar = revision.nuevo_valor_paquete
            if revision.nuevo_valor_dai:
                impuesto.dai_porcentaje = revision.nuevo_valor_dai

            # Insertar nuevo registro de cambios
            revision_obj = RevisionSat(
                valor_paquete_previo = paquete.valor_producto_dolar,
                valor_dai_previo = impuesto.dai_porcentaje,
                motivo_cambio = revision.motivo_cambio,
                usuario_id = user
            )
            session.add(revision_obj)

            recalcular_valores_dependientes(paquete, impuesto)

            # Crear seguimiento para los paquetes modificados
            seguimiento_obj = SeguimientoPaquete(
                    estado_actual = 'liberado',
                    motivo_cambio ='Revision SAT finalizada',
                    paquete_id = paquete_id,
                    usuario_id = user
                )
            session.add(seguimiento_obj)
        
        session.commit()

    except IntegrityError as e:
        session.rollback()
        raise ValueError("Error de integridad: posible registro duplicado o violacion de restricciones.") from e

    except DataError as e:
        session.rollback()
        raise ValueError("Error de datos: campos nulos, incompletos o tipo de datos inadecuado.") from e

    except OperationalError as e:
        session.rollback()
        raise Exception("Error operacional en la base de datos.") from e

    except Exception as e:
        session.rollback()
        raise Exception(f"Error inesperado: {str(e)}") from e

    finally:
        session.close()


def recalcular_valores_dependientes(paquete: Paquete, impuesto: Impuesto):
    session = Session()
    try:
        # recalcular valores dependientes en Gasto
        cambioDolar = 7.98

        # Recalcular valores para el impuesto
        impuesto.monto_iva_dolar = paquete.valor_producto_dolar * 0.12
        impuesto.monto_dai_dolar = paquete.valor_producto_dolar * (impuesto.dai_porcentaje / 100)
        
        # Buscar y actualizar el gasto asociado, si existe
        gasto = session.query(Gasto).filter(Gasto.paquete_id == paquete.id_paquete).one_or_none()
        if gasto:
            gasto.monto_iva_quetzal = impuesto.monto_iva_dolar * cambioDolar
            gasto.monto_dai_quetzal = impuesto.monto_dai_dolar * cambioDolar
            gasto.valor_quetzal = paquete.valor_producto_dolar * cambioDolar
            gasto.gasto_total = gasto.monto_iva_quetzal + gasto.monto_dai_quetzal + gasto.monto_flete + gasto.monto_combex

        session.commit()

    except IntegrityError as e:
        session.rollback()
        raise ValueError("Error de integridad: posible registro duplicado o violacion de restricciones.") from e

    except DataError as e:
        session.rollback()
        raise ValueError("Error de datos: campos nulos, incompletos o tipo de datos inadecuado.") from e

    except OperationalError as e:
        session.rollback()
        raise Exception("Error operacional en la base de datos.") from e

    except Exception as e:
        session.rollback()
        raise Exception(f"Error inesperado: {str(e)}") from e

    finally:
        session.close()