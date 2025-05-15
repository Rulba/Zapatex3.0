from app import db

class Stock(db.Model):
    __tablename__ = 'stock'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    producto = db.Column(db.String(100), nullable=False)
    sucursal = db.Column(db.String(100), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "producto": self.producto,
            "sucursal": self.sucursal,
            "cantidad": self.cantidad,
            "precio": self.precio
        }

