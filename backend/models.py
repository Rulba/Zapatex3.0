from extensions import db
from flask_sqlalchemy import SQLAlchemy
from flask import Flask

class Stock(db.Model):
    __tablename__ = 'stock'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    producto = db.Column(db.String(100), nullable=False)
    sucursal = db.Column(db.String(100), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio = db.Column(db.Float, nullable=False)
    
    imagen_base64 = db.Column(db.Text, nullable=True)     # Se mantiene por compatibilidad
    imagen_ruta = db.Column(db.String(200), nullable=True) # Nueva columna para archivo

    def to_dict(self):
        return {
            "id": self.id,
            "producto": self.producto,
            "sucursal": self.sucursal,
            "cantidad": self.cantidad,
            "precio": self.precio,
            "imagen_base64": self.imagen_base64,
            "imagen_ruta": f"/static/images/{self.imagen_ruta}" if self.imagen_ruta else None
        }
