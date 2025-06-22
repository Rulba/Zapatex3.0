from flask import Flask
from extensions import db
from models import Stock
import base64
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///zapatex.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def cargar_imagen_base64(ruta_imagen):
    with open(ruta_imagen, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

with app.app_context():
    db.drop_all()
    db.create_all()

    ruta_imagenes = os.path.join(os.path.dirname(__file__), "static", "images")

    productos = [
        # ZapatoX en distintas sucursales
        Stock(
            sucursal='Sucursal 1',
            producto='ZapatoX',
            cantidad=31,
            precio=34990,
            imagen_base64=cargar_imagen_base64(os.path.join(ruta_imagenes, "zapatox.png"))
        ),
        Stock(
            sucursal='Sucursal 2',
            producto='ZapatoX',
            cantidad=0,
            precio=33990,
            imagen_base64=cargar_imagen_base64(os.path.join(ruta_imagenes, "zapatox.png"))
        ),
        Stock(
            sucursal='Sucursal 3',
            producto='ZapatoX',
            cantidad=100,
            precio=35990,
            imagen_base64=cargar_imagen_base64(os.path.join(ruta_imagenes, "zapatoX.png"))
        ),
        Stock(
            sucursal='Casa Matriz',
            producto='ZapatoX',
            cantidad=10,
            precio=34990,
            imagen_base64=cargar_imagen_base64(os.path.join(ruta_imagenes, "zapatoX.png"))
        ),

        # Zapatilla Y
        Stock(
            sucursal='Sucursal 1',
            producto='Zapatilla Y',
            cantidad=5,
            precio=27990,
            imagen_base64=cargar_imagen_base64(os.path.join(ruta_imagenes, "zapatillay.png"))
        ),
        Stock(
            sucursal='Sucursal 2',
            producto='Zapatilla Y',
            cantidad=18,
            precio=28990,
            imagen_base64=cargar_imagen_base64(os.path.join(ruta_imagenes, "zapatillaY.png"))
        ),
        Stock(
            sucursal='Sucursal 3',
            producto='Zapatilla Y',
            cantidad=0,
            precio=26990,
            imagen_base64=cargar_imagen_base64(os.path.join(ruta_imagenes, "zapatillaY.png"))
        ),
        Stock(
            sucursal='Casa Matriz',
            producto='Zapatilla Y',
            cantidad=25,
            precio=29990,
            imagen_base64=cargar_imagen_base64(os.path.join(ruta_imagenes, "zapatillaY.png"))
        ),

        # BotínZ
        Stock(
            sucursal='Sucursal 1',
            producto='BotínZ',
            cantidad=50,
            precio=44990,
            imagen_base64=cargar_imagen_base64(os.path.join(ruta_imagenes, "botinz.png"))
        ),
        Stock(
            sucursal='Sucursal 2',
            producto='BotínZ',
            cantidad=5,
            precio=45990,
            imagen_base64=cargar_imagen_base64(os.path.join(ruta_imagenes, "botinZ.png"))
        ),
        Stock(
            sucursal='Casa Matriz',
            producto='BotínZ',
            cantidad=15,
            precio=43990,
            imagen_base64=cargar_imagen_base64(os.path.join(ruta_imagenes, "botinZ.png"))
        ),

        # Sandalia K
        Stock(
            sucursal='Sucursal 3',
            producto='Sandalia K',
            cantidad=30,
            precio=19990,
            imagen_base64=cargar_imagen_base64(os.path.join(ruta_imagenes, "sandaliaK.png"))
        ),
        Stock(
            sucursal='Sucursal 1',
            producto='Sandalia K',
            cantidad=20,
            precio=20990,
            imagen_base64=cargar_imagen_base64(os.path.join(ruta_imagenes, "sandaliaK.png"))
        ),

        # Zapato Ejecutivo
        Stock(
            sucursal='Casa Matriz',
            producto='Zapato Ejecutivo',
            cantidad=12,
            precio=54990,
            imagen_base64=cargar_imagen_base64(os.path.join(ruta_imagenes, "zapatoejecutivo.png"))
        ),
    ]

    db.session.add_all(productos)
    db.session.commit()

    print("📦 Base de datos inicializada con productos y sus imágenes.")
