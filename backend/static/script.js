let productos = [];

async function cargarDatos() {
  const res = await fetch('/api/stock');
  const data = await res.json();

  productos = [...data.sucursales];
  if (data.casa_matriz) {
    productos.push(data.casa_matriz);
  }

  mostrarProductos();
}

function mostrarProductos(filtro = '') {
  const lista = document.getElementById('sucursales-list');
  const select = document.getElementById('sucursal');
  const matrizDiv = document.getElementById('casa-matriz');

  lista.innerHTML = '';
  select.innerHTML = '';
  matrizDiv.innerHTML = '';
  document.getElementById('alerta-stock').style.display = 'none';

  const filtroLower = filtro.toLowerCase();
  const productosFiltrados = filtro
    ? productos.filter(p => p.producto.toLowerCase().includes(filtroLower))
    : productos;

  const productosAgrupados = {};
  productosFiltrados.forEach(p => {
    if (!productosAgrupados[p.producto]) {
      productosAgrupados[p.producto] = [];
    }
    productosAgrupados[p.producto].push(p);
  });

  for (const nombreProducto in productosAgrupados) {
    const grupo = document.createElement('div');
    grupo.className = 'producto-group';

    // Header con flecha
    const header = document.createElement('div');
    header.className = 'producto-header';

    const flecha = document.createElement('span');
    flecha.textContent = '▶ ';
    flecha.style.display = 'inline-block';
    flecha.style.transition = 'transform 0.2s ease';
    flecha.className = 'flecha';

    header.appendChild(flecha);
    header.appendChild(document.createTextNode(nombreProducto));

    // Contenedor de sucursales oculto
    const contenedorSucursales = document.createElement('div');
    contenedorSucursales.className = 'producto-detalle';
    contenedorSucursales.style.display = 'none';

    productosAgrupados[nombreProducto].forEach(s => {
      const div = document.createElement('div');
      div.className = 'sucursal';
      div.textContent = `${s.sucursal}: Cant: ${s.cantidad} | Precio: ${s.precio}`;
      contenedorSucursales.appendChild(div);

      if (![...select.options].some(opt => opt.value === s.sucursal)) {
        const opt = document.createElement('option');
        opt.value = s.sucursal;
        opt.textContent = s.sucursal;
        select.appendChild(opt);
      }

      if (s.sucursal.toLowerCase() === 'casa matriz') {
        matrizDiv.textContent = `Cant: ${s.cantidad} | Precio: ${s.precio}`;
      }

      if (s.cantidad === 0) {
        const alerta = document.getElementById('alerta-stock');
        alerta.style.display = 'block';
        alerta.textContent = `Stock bajo en ${s.sucursal}`;
      }
    });

    // Toggle visibilidad
    header.addEventListener('click', () => {
      const visible = contenedorSucursales.style.display === 'block';
      contenedorSucursales.style.display = visible ? 'none' : 'block';
      flecha.style.transform = visible ? 'rotate(0deg)' : 'rotate(90deg)';
    });

    grupo.appendChild(header);
    grupo.appendChild(contenedorSucursales);
    lista.appendChild(grupo);
  }
}




document.getElementById('buscar').addEventListener('input', e => {
  mostrarProductos(e.target.value);
});

document.getElementById('calcular').addEventListener('click', async () => {
  const cantidad = parseInt(document.getElementById('cantidad').value);
  const nombreProducto = document.querySelector('.producto-header')?.textContent;

  if (!nombreProducto) {
    alert('Primero busca y selecciona un producto válido');
    return;
  }

  const coincidencias = productos.filter(p =>
    p.producto.toLowerCase() === nombreProducto.toLowerCase() &&
    p.cantidad > 0
  );

  const stockTotal = coincidencias.reduce((sum, s) => sum + s.cantidad, 0);

  if (cantidad > stockTotal) {
    alert(`No hay suficiente stock disponible. Solo hay ${stockTotal} unidades en total.`);
    return;
  }

  let restante = cantidad;
  let totalCLP = 0;
  let detalle = [];

  for (const s of coincidencias) {
    if (restante === 0) break;

    const usar = Math.min(s.cantidad, restante);
    totalCLP += usar * s.precio;
    detalle.push(`${usar} u. desde ${s.sucursal}`);
    restante -= usar;
  }

  const res = await fetch(`/api/usd?clp=${totalCLP}`);
  const data = await res.json();

  document.getElementById('total').innerHTML =
    `Total: ${totalCLP} CLP | USD: ${data.usd}<br><small>${detalle.join(', ')}</small>`;
});

document.getElementById('vender').addEventListener('click', async () => {
  const cantidad = parseInt(document.getElementById('cantidad').value);
  const nombreProducto = document.querySelector('.producto-header')?.textContent;

  if (!nombreProducto) {
    alert('Selecciona un producto válido primero');
    return;
  }

  const confirmacion = confirm('¿Ir a Transbank para pagar?');
  if (!confirmacion) return;

  const res = await fetch('/iniciar_pago', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ producto: nombreProducto, cantidad: cantidad })
  });

  const data = await res.json();
  if (data.url && data.token) {
    // Redirigir a Webpay (modo prueba)
    const form = document.createElement('form');
    form.action = data.url;
    form.method = 'POST';

    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = 'token_ws';
    input.value = data.token;
    form.appendChild(input);

    document.body.appendChild(form);
    form.submit();
  } else {
    alert('Error al iniciar el pago.');
  }
});


  const confirmacion = confirm('¿Confirmar pago con Transbank?');
  if (!confirmacion) return;

  const res = await fetch('/venta', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ producto: nombreProducto, cantidad: cantidad })
  });

  const data = await res.json();

  if (res.ok) {
    alert('✅ Pago exitoso con Transbank.\nStock actualizado.');
    await cargarDatos();
    document.getElementById('total').textContent = '';
  } else {
    alert('❌ Error en venta: ' + (data.error || 'Desconocido'));
  }

document.addEventListener('DOMContentLoaded', cargarDatos);
