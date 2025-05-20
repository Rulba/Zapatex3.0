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
