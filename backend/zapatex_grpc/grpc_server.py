import grpc
from concurrent import futures
import productos_pb2
import productos_pb2_grpc
import productos_logic as logic

class ProductoService(productos_pb2_grpc.ProductoServiceServicer):
    def AgregarProducto(self, request, context):
        data = {
            "id": request.id,
            "nombre": request.nombre,
            "precio": request.precio,
            "imagen_base64": request.imagen_base64,
            "stock": [{"sucursal": s.sucursal, "cantidad": s.cantidad} for s in request.stock]
        }
        exito, mensaje = logic.agregar_producto(data)
        return productos_pb2.ProductoResponse(
            exito=exito,
            mensaje=mensaje,
            producto=request
        )

    def ObtenerProducto(self, request, context):
        prod = logic.obtener_producto(request.id)
        if not prod:
            return productos_pb2.ProductoResponse(
                exito=False,
                mensaje="Producto no encontrado"
            )
        stock = [productos_pb2.StockPorSucursal(sucursal=s['sucursal'], cantidad=s['cantidad']) for s in prod['stock']]
        producto = productos_pb2.ProductoRequest(
            id=prod['id'],
            nombre=prod['nombre'],
            precio=prod['precio'],
            imagen_base64=prod['imagen_base64'],
            stock=stock
        )
        return productos_pb2.ProductoResponse(
            exito=True,
            mensaje="Producto encontrado",
            producto=producto
        )

    def ListarProductos(self, request, context):
        lista = logic.listar_productos()
        productos_proto = []
        for p in lista:
            stock = [productos_pb2.StockPorSucursal(sucursal=s['sucursal'], cantidad=s['cantidad']) for s in p['stock']]
            productos_proto.append(productos_pb2.ProductoRequest(
                id=p['id'],
                nombre=p['nombre'],
                precio=p['precio'],
                imagen_base64=p['imagen_base64'],
                stock=stock
            ))
        return productos_pb2.ListaProductos(productos=productos_proto)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    productos_pb2_grpc.add_ProductoServiceServicer_to_server(ProductoService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Servidor gRPC corriendo en puerto 50051...")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
