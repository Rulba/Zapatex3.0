let productos = [];
let productoSeleccionado = '';

async function cargarDatos() {
  const res = await fetch('/api/stock');
  const data = await res.json();

  productos = [...data.sucursales];
  if (data.casa_matriz) productos.push(data.casa_matriz);

  window.productos = productos;
  mostrarProductos();
}

function mostrarProductos(filtro = '') {
  const lista = document.getElementById('sucursales-list');
  const select = document.getElementById('sucursal');
  const matrizDiv = document.getElementById('casa-matriz');
  const alerta = document.getElementById('alerta-stock');

  lista.innerHTML = '';
  select.innerHTML = '';
  matrizDiv.innerHTML = '';
  alerta.style.display = 'none';

  const filtroLower = filtro.toLowerCase();
  const productosFiltrados = filtro.trim()
    ? productos.filter(p => p.producto.toLowerCase().includes(filtroLower))
    : productos;

  const productosAgrupados = {};
  productosFiltrados.forEach(p => {
    if (!productosAgrupados[p.producto]) {
      productosAgrupados[p.producto] = [];
    }
    productosAgrupados[p.producto].push(p);
  });

  const sucursalesAgregadas = new Set();

  for (const nombreProducto in productosAgrupados) {
    const grupo = document.createElement('div');
    grupo.className = 'producto-group';

    const header = document.createElement('div');
    header.className = 'producto-header';

    const flecha = document.createElement('span');
    flecha.textContent = '▶ ';
    flecha.className = 'flecha';
    flecha.style.display = 'inline-block';
    flecha.style.transition = 'transform 0.2s ease';

    header.appendChild(flecha);
    header.appendChild(document.createTextNode(nombreProducto));

    const contenedorSucursales = document.createElement('div');
    contenedorSucursales.className = 'producto-detalle';
    contenedorSucursales.style.display = 'none';

    productosAgrupados[nombreProducto].forEach(s => {
      const div = document.createElement('div');
      div.className = 'sucursal';
      div.textContent = `${s.sucursal}: Cant: ${s.cantidad} | Precio: ${s.precio}`;
      contenedorSucursales.appendChild(div);

      if (!sucursalesAgregadas.has(s.sucursal)) {
        sucursalesAgregadas.add(s.sucursal);
        const opt = document.createElement('option');
        opt.value = s.sucursal;
        opt.textContent = s.sucursal;
        select.appendChild(opt);
      }

      if (s.sucursal.toLowerCase() === 'casa matriz') {
        matrizDiv.textContent = `Cant: ${s.cantidad} | Precio: ${s.precio}`;
      }

      if (s.cantidad === 0) {
        alerta.style.display = 'block';
        alerta.textContent = `Stock bajo en ${s.sucursal}`;
      }
    });

    header.addEventListener('click', () => {
  const visible = contenedorSucursales.style.display === 'block';
  contenedorSucursales.style.display = visible ? 'none' : 'block';
  flecha.style.transform = visible ? 'rotate(0deg)' : 'rotate(90deg)';

  if (!visible) {
    productoSeleccionado = nombreProducto;  // ← Guardamos el producto seleccionado
  }
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
  const nombreProducto = productoSeleccionado;


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
    alert(`No hay suficiente stock. Solo hay ${stockTotal} unidades disponibles.`);
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
  const nombreProducto = productoSeleccionado;

  if (!nombreProducto || isNaN(cantidad) || cantidad <= 0) {
    alert('Selecciona un producto válido y una cantidad mayor a 0');
    return;
  }

  const confirmacion = confirm('¿Confirmar pago con Transbank?');
  if (!confirmacion) return;

  try {
    const res = await fetch('/iniciar_pago', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ producto: nombreProducto, cantidad: cantidad })
    });

    const text = await res.text(); // primero lo leemos como texto por si no es JSON

    try {
      const data = JSON.parse(text); // si es JSON, lo parseamos
      console.log("✅ Respuesta de iniciar_pago:", data);

      if (data.url && data.token) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = data.url;

        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'token_ws';
        input.value = data.token;

        form.appendChild(input);
        document.body.appendChild(form);
        form.submit();
      } else {
        console.error("❌ Respuesta no contiene token o URL:", data);
        alert('❌ Error iniciando pago con Transbank (datos incompletos).');
      }

    } catch (jsonError) {
      console.error("❌ No se pudo parsear como JSON:", text);
      alert('❌ Error inesperado del servidor (no es JSON). Revisa consola o servidor.');
    }

  } catch (error) {
    console.error("❌ Error en la solicitud de pago:", error);
    alert('❌ Error al intentar iniciar el pago. Revisa tu conexión o contacta soporte.');
  }
});

document.addEventListener('DOMContentLoaded', cargarDatos);
