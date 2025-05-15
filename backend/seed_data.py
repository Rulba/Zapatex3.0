from app import app, db
from models import Stock

# Ejecutar dentro del contexto de la app Flask
with app.app_context():
    # Primero borramos todo para evitar duplicados si quieres
    db.drop_all()
    db.create_all()

    # Lista de datos ejemplo (producto, sucursal, cantidad, precio en CLP)
    datos_prueba = [
        Stock(producto="Zapato Deportivo", sucursal="Casa Matriz", cantidad=50, precio=35000),
        Stock(producto="Zapato Deportivo", sucursal="Sucursal Norte", cantidad=20, precio=36000),
        Stock(producto="Zapato Deportivo", sucursal="Sucursal Sur", cantidad=30, precio=35500),
        Stock(producto="Sandalia Verano", sucursal="Casa Matriz", cantidad=40, precio=15000),
        Stock(producto="Sandalia Verano", sucursal="Sucursal Norte", cantidad=15, precio=16000),
        Stock(producto="Sandalia Verano", sucursal="Sucursal Sur", cantidad=25, precio=15500),
        Stock(producto="Botín Cuero", sucursal="Casa Matriz", cantidad=60, precio=45000),
        Stock(producto="Botín Cuero", sucursal="Sucursal Norte", cantidad=22, precio=46000),
        Stock(producto="Botín Cuero", sucursal="Sucursal Sur", cantidad=35, precio=45500),
    ]

    # Agregar a la sesión y guardar
    for item in datos_prueba:
        db.session.add(item)
    db.session.commit()

    print("Datos de prueba insertados correctamente.")
