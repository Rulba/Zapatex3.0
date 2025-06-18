productos = {}

def agregar_producto(data):
    productos[data['id']] = data
    return True, "Producto agregado"

def obtener_producto(id):
    return productos.get(id, None)

def listar_productos():
    return list(productos.values())
