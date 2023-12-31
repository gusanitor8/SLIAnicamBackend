from config.database import Session
from dataModels.impuesto import ImpuestoBase
from models.impuesto_table import Impuesto
from models.paquete_table import Paquete
from models.seguimiento_paquete_table import SeguimientoPaquete
from sqlalchemy.exc import IntegrityError, DataError, OperationalError, NoResultFound




def carga_impuestos(impuesto: ImpuestoBase, user: int):
    try:
        session = Session()

        # Verificar si ya existe un impuesto para el paquete dado
        impuesto_existente = session.query(Impuesto).filter_by(paquete_id=impuesto.paquete_id,).first()

        if impuesto_existente:
            raise ValueError("Ya existe un impuesto para el paquete y poliza proporcionados.")

        paquete = session.query(Paquete).filter(Paquete.id_paquete == impuesto.paquete_id).one()
        
        iva_dolar = paquete.valor_producto_dolar * 0.12
        dai_dolar = paquete.valor_producto_dolar * (impuesto.dai_porcentaje / 100)

        # Crear el objeto Impuesto
        impuesto_obj = Impuesto(
            # id_impuesto autogenerado
            paquete_id = impuesto.paquete_id,
            monto_iva_dolar = iva_dolar,
            dai_porcentaje = impuesto.dai_porcentaje,
            monto_dai_dolar = dai_dolar,
            poliza = impuesto.poliza,
            partida = impuesto.partida,
            consignatario = impuesto.consignatario
            # fecha_impuesto autogenerada
        )
        
        # Insertar el nuevo impuesto en la base de datos
        session.add(impuesto_obj)


        # Creacion e insercion de registro de seguimiento para paquete
        seguimiento_obj = SeguimientoPaquete(
                estado_actual='gestion aduana',
                motivo_cambio='Carga de impuestos',
                paquete_id = impuesto.paquete_id,
                usuario_id = user  
            )
        session.add(seguimiento_obj)



        session.commit()
    
    except IntegrityError as e:
        session.rollback()
        raise ValueError("Error de integridad: posible registro duplicado o violacion de restricciones.") from e
    
    except NoResultFound:
        session.rollback()
        raise ValueError("Paquete no encontrado con el ID proporcionado.")

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
        # Asegurarse de cerrar la sesion de la base de datos
        session.close()