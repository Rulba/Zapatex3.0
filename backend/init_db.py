from app import db, Stock

db.create_all()

# Agregar datos de prueba
if not Stock.query.first():
    db.session.add(Stock(sucursal='Sucursal 1', cantidad=31, precio=333))
    db.session.add(Stock(sucursal='Sucursal 2', cantidad=23, precio=222))
    db.session.add(Stock(sucursal='Sucursal 3', cantidad=100, precio=1111))
    db.session.add(Stock(sucursal='Casa Matriz', cantidad=10, precio=999))
    db.session.commit()

print("Base de datos creada con datos de prueba.")
