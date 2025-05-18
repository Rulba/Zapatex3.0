document.getElementById('buscar').addEventListener('input', filtrarSucursales);

function filtrarSucursales() {
  const busqueda = document.getElementById('buscar').value.toLowerCase();
  const lista = document.getElementById('sucursales-list');
  const select = document.getElementById('sucursal');

  // Limpiar lista
  lista.innerHTML = '';
  select.innerHTML = '';

  const filtrados = productos.filter(p =>
    p.producto.toLowerCase().includes(busqueda)
  );

  filtrados.forEach((s) => {
    const div = document.createElement('div');
    div.className = 'sucursal';
    div.textContent = `${s.sucursal}: Cant: ${s.cantidad} | Precio: ${s.precio}`;
    lista.appendChild(div);

    const opt = document.createElement('option');
    opt.value = s.sucursal;
    opt.textContent = s.sucursal;
    select.appendChild(opt);
  });

  // También mostrar Casa Matriz si aplica
  const matriz = productos.find(p =>
    p.sucursal.toLowerCase() === 'casa matriz' &&
    p.producto.toLowerCase().includes(busqueda)
  );
  if (matriz) {
    document.getElementById('casa-matriz').textContent =
      `Cant: ${matriz.cantidad} | Precio: ${matriz.precio}`;
  } else {
    document.getElementById('casa-matriz').textContent = '';
  }
}
