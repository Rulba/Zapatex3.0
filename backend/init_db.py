from app import app, db
import models
from models import Stock

with app.app_context():
    db.create_all()
    print("Base de datos creada correctamente.")

    # Datos de ejemplo
    productos = [
        Stock(producto='Zapato Casual', sucursal='Sucursal 1', cantidad=31, precio=333),
        Stock(producto='Zapato Casual', sucursal='Sucursal 2', cantidad=23, precio=222),
        Stock(producto='Zapato Casual', sucursal='Sucursal 3', cantidad=100, precio=1111),
        Stock(producto='Zapato Casual', sucursal='Casa Matriz', cantidad=10, precio=999),
    ]

    # Insertar datos
    db.session.bulk_save_objects(productos)
    db.session.commit()
    print("Datos iniciales insertados correctamente.")
