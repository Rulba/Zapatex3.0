let productos = [];
let productoSeleccionado = '';

async function cargarDatos() {
  try {
    const res = await fetch('/api/stock');
    if (!res.ok) throw new Error(`Error al cargar stock: ${res.status}`);
    const data = await res.json();

    productos = [...data.sucursales];
    if (data.casa_matriz) productos.push(data.casa_matriz);

    window.productos = productos;
    console.log("✅ Productos cargados:", window.productos);

    mostrarProductos();
  } catch (error) {
    alert('Error cargando productos. Revisa consola.');
    console.error(error);
  }
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
  alerta.textContent = '';

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

    if (nombreProducto === productoSeleccionado) {
      grupo.classList.add('seleccionado');
      grupo.style.backgroundColor = '#eef6ff';
      grupo.style.border = '1px solid #3399ff';
    } else {
      grupo.style.backgroundColor = '';
      grupo.style.border = '';
    }

    const header = document.createElement('div');
    header.className = 'producto-header';
    header.style.cursor = 'pointer';

    const flecha = document.createElement('span');
    flecha.textContent = '▶ ';
    flecha.className = 'flecha';
    flecha.style.display = 'inline-block';
    flecha.style.transition = 'transform 0.2s ease';

    // Si este producto está seleccionado, rotamos la flecha
    if (nombreProducto === productoSeleccionado) {
      flecha.style.transform = 'rotate(90deg)';
    }

    header.appendChild(flecha);
    header.appendChild(document.createTextNode(nombreProducto));

    const contenedorSucursales = document.createElement('div');
    contenedorSucursales.className = 'producto-detalle';
    contenedorSucursales.style.display = (nombreProducto === productoSeleccionado) ? 'block' : 'none';

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

      if (s.cantidad <= 2) {
        alerta.style.display = 'block';
        alerta.textContent = `⚠️ Stock bajo en ${s.sucursal}: quedan ${s.cantidad} unidades.`;
      }
    });

    header.addEventListener('click', () => {
      const visible = contenedorSucursales.style.display === 'block';

      // Si estaba visible, lo cerramos y deseleccionamos
      if (visible) {
        contenedorSucursales.style.display = 'none';
        flecha.style.transform = 'rotate(0deg)';
        productoSeleccionado = '';
      } else {
        // Si no estaba visible, abrimos solo este, cerrando otros
        productoSeleccionado = nombreProducto;
      }

      // Vuelve a renderizar para actualizar todo el estado (flechas, resaltado, detalle)
      mostrarProductos(document.getElementById('buscar').value);

      actualizarBotones();
    });

    grupo.appendChild(header);
    grupo.appendChild(contenedorSucursales);
    lista.appendChild(grupo);
  }

  actualizarBotones();
}

function actualizarBotones() {
  const btnCalcular = document.getElementById('calcular');
  const btnVender = document.getElementById('vender');
  if (productoSeleccionado) {
    btnCalcular.disabled = false;
    btnVender.disabled = false;
  } else {
    btnCalcular.disabled = true;
    btnVender.disabled = true;
  }
}

document.getElementById('buscar').addEventListener('input', e => {
  mostrarProductos(e.target.value);
});

document.getElementById('calcular').addEventListener('click', async () => {
  const cantidad = parseInt(document.getElementById('cantidad').value);
  const nombreProducto = productoSeleccionado;

  if (!nombreProducto || isNaN(cantidad) || cantidad <= 0) {
    alert('Selecciona un producto válido y una cantidad mayor a 0');
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

  try {
    const res = await fetch(`/api/usd?clp=${totalCLP}`);
    if (!res.ok) throw new Error(`Error en conversión USD: ${res.status}`);
    const data = await res.json();

    document.getElementById('total').innerHTML =
      `Total: ${totalCLP} CLP | USD: ${data.usd}<br><small>${detalle.join(', ')}</small>`;
  } catch (error) {
    alert('Error obteniendo tipo de cambio USD. Revisa consola.');
    console.error(error);
  }
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

    const text = await res.text();

    try {
      const data = JSON.parse(text);
      console.log("✅ Respuesta de iniciar_pago:", data);

      if (data.url && data.token) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = data.url;

        const tokenInput = document.createElement('input');
        tokenInput.type = 'hidden';
        tokenInput.name = 'token_ws';
        tokenInput.value = data.token;
        form.appendChild(tokenInput);

        const productoInput = document.createElement('input');
        productoInput.type = 'hidden';
        productoInput.name = 'producto';
        productoInput.value = nombreProducto;
        form.appendChild(productoInput);

        const cantidadInput = document.createElement('input');
        cantidadInput.type = 'hidden';
        cantidadInput.name = 'cantidad';
        cantidadInput.value = cantidad;
        form.appendChild(cantidadInput);

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
