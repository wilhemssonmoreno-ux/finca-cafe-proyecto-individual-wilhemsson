'use strict';

/* ---------- Utilidades ---------- */
const $ = (s, r = document) => r.querySelector(s);
const esc = (v) => String(v ?? '').replace(/[&<>"']/g, (c) =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const num = (n, d = 0) => Number(n).toLocaleString('es-HN', { minimumFractionDigits: d, maximumFractionDigits: d });
const lempiras = (n) => (n == null ? '—' : 'L ' + num(n, 2));
const fecha = (iso) => (iso ? iso.split('-').reverse().join('/') : '');
const hoy = () => { const d = new Date(); return new Date(d - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10); };
const haceDias = (n) => { const d = new Date(); d.setDate(d.getDate() - n); return new Date(d - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10); };
const nombreMes = (aaaamm) => {
  const [a, m] = aaaamm.split('-').map(Number);
  return new Date(a, m - 1, 1).toLocaleDateString('es-HN', { month: 'long', year: 'numeric' });
};

let token = localStorage.getItem('finca_token');

/* ---------- Comunicación con la API ---------- */
async function api(ruta, { metodo = 'GET', cuerpo, crudo = false } = {}) {
  const cabeceras = {};
  if (cuerpo) cabeceras['Content-Type'] = 'application/json';
  if (token) cabeceras.Authorization = 'Bearer ' + token;
  const r = await fetch(ruta, { method: metodo, headers: cabeceras, body: cuerpo ? JSON.stringify(cuerpo) : undefined });
  if (r.status === 401 && ruta !== '/auth/login') {
    cerrarSesion();
    throw new Error('Tu sesión terminó. Entra de nuevo.');
  }
  if (!r.ok) {
    let mensaje = 'No se pudo completar la acción. Intenta otra vez.';
    try {
      const j = await r.json();
      if (typeof j.detail === 'string') mensaje = j.detail;
    } catch (_) { /* respuesta sin JSON */ }
    throw new Error(mensaje);
  }
  return crudo ? r : r.json();
}

function aviso(texto, tipo = 'ok') {
  const el = document.createElement('div');
  el.className = 'aviso ' + tipo;
  el.textContent = texto;
  $('#avisos').append(el);
  setTimeout(() => el.remove(), tipo === 'ok' ? 3500 : 6000);
}

async function descargarCSV(recurso, params = {}) {
  try {
    const q = new URLSearchParams(Object.entries(params).filter(([, v]) => v)).toString();
    const r = await api(`/exportar/${recurso}${q ? '?' + q : ''}`, { crudo: true });
    const url = URL.createObjectURL(await r.blob());
    const a = Object.assign(document.createElement('a'), { href: url, download: `${recurso}_${hoy()}.csv` });
    document.body.append(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
    aviso('Archivo CSV descargado.');
  } catch (e) { aviso(e.message, 'mal'); }
}

/* ---------- Definición de cada tabla ---------- */
const opcionesDe = (ruta, etiqueta) => async () => (await api(ruta)).map((x) => [x.id, etiqueta(x)]);

const RECURSOS = {
  cosechas: {
    titulo: 'Cosechas', ruta: '/cosechas', nuevo: 'Nueva cosecha', guardado: 'Cosecha guardada.', eliminado: 'Cosecha eliminada.',
    buscarEn: 'lote, trabajador o fecha', filtrosFecha: true,
    vacio: 'Todavía no hay cosechas. Registra la primera con «Nueva cosecha».',
    desc: (f) => `la cosecha de ${f.trabajador_nombre} del ${fecha(f.fecha)}`,
    columnas: [
      { t: 'Fecha', k: 'fecha', f: fecha },
      { t: 'Lote', k: 'lote_nombre' },
      { t: 'Trabajador', k: 'trabajador_nombre' },
      { t: 'Latas', k: 'latas', num: true, f: (v) => num(v) },
      { t: 'Precio por lata', k: 'precio_por_lata', num: true, f: lempiras },
      { t: 'Pago', k: 'pago', num: true, f: lempiras },
    ],
    campos: [
      { k: 'lote_id', t: 'Lote', tipo: 'select', opciones: opcionesDe('/lotes', (l) => `${l.nombre} (${l.variedad})`) },
      { k: 'trabajador_id', t: 'Trabajador', tipo: 'select', opciones: opcionesDe('/trabajadores', (t) => t.nombre) },
      { k: 'fecha', t: 'Fecha', tipo: 'date', inicial: hoy },
      { k: 'latas', t: 'Latas cortadas', tipo: 'int', min: 1, ayuda: 'El pago se calcula con la tarifa vigente de esa fecha.' },
    ],
  },
  lotes: {
    titulo: 'Lotes', ruta: '/lotes', nuevo: 'Nuevo lote', guardado: 'Lote guardado.', eliminado: 'Lote eliminado.',
    buscarEn: 'nombre o variedad',
    vacio: 'Todavía no hay lotes. Crea el primero con «Nuevo lote».',
    desc: (f) => `el lote «${f.nombre}»`,
    columnas: [
      { t: 'Nombre', k: 'nombre' },
      { t: 'Variedad', k: 'variedad' },
      { t: 'Hectáreas', k: 'hectareas', num: true, f: (v) => num(v, 2) },
    ],
    campos: [
      { k: 'nombre', t: 'Nombre del lote', tipo: 'text' },
      { k: 'variedad', t: 'Variedad de café', tipo: 'text' },
      { k: 'hectareas', t: 'Hectáreas', tipo: 'number', paso: '0.1', min: 0.1 },
    ],
  },
  trabajadores: {
    titulo: 'Trabajadores', ruta: '/trabajadores', nuevo: 'Nuevo trabajador', guardado: 'Trabajador guardado.', eliminado: 'Trabajador eliminado.',
    buscarEn: 'nombre, identidad o teléfono',
    vacio: 'Todavía no hay trabajadores. Agrega el primero con «Nuevo trabajador».',
    desc: (f) => `a ${f.nombre}`,
    columnas: [
      { t: 'Nombre', k: 'nombre' },
      { t: 'Identidad', k: 'identidad' },
      { t: 'Teléfono', k: 'telefono' },
    ],
    campos: [
      { k: 'nombre', t: 'Nombre completo', tipo: 'text' },
      { k: 'identidad', t: 'Identidad', tipo: 'text', placeholder: '0301-1990-12345', ayuda: 'Con o sin guiones.' },
      { k: 'telefono', t: 'Teléfono', tipo: 'text', placeholder: '9876-5432', ayuda: '8 dígitos.' },
    ],
  },
  tarifas: {
    titulo: 'Tarifas', ruta: '/tarifas', nuevo: 'Nueva tarifa', guardado: 'Tarifa guardada.', eliminado: 'Tarifa eliminada.',
    buscarEn: 'temporada',
    vacio: 'Todavía no hay tarifas. Sin una tarifa vigente no se pueden registrar cosechas.',
    desc: (f) => `la tarifa «${f.temporada}»`,
    columnas: [
      { t: 'Temporada', k: 'temporada' },
      { t: 'Precio por lata', k: 'precio_por_lata', num: true, f: lempiras },
      { t: 'Desde', k: 'fecha_inicio', f: fecha },
      { t: 'Hasta', k: 'fecha_fin', f: fecha },
      { t: 'Estado', h: (f) => (f.fecha_inicio <= hoy() && hoy() <= f.fecha_fin ? '<span class="etiqueta">Vigente hoy</span>' : '') },
    ],
    campos: [
      { k: 'temporada', t: 'Temporada', tipo: 'text', placeholder: 'Cosecha 2027-2028' },
      { k: 'precio_por_lata', t: 'Precio por lata (L)', tipo: 'number', paso: '0.5', min: 0.5 },
      { k: 'fecha_inicio', t: 'Vigente desde', tipo: 'date' },
      { k: 'fecha_fin', t: 'Vigente hasta', tipo: 'date', ayuda: 'Las fechas de dos tarifas no pueden traslaparse.' },
    ],
  },
  produccion: {
    titulo: 'Café en bodega', ruta: '/produccion', nuevo: 'Registrar café procesado', singular: 'ingreso de café',
    guardado: 'Ingreso de café guardado.', eliminado: 'Ingreso de café eliminado.', banner: true,
    buscarEn: 'lote o fecha',
    vacio: 'Todavía no hay café en bodega. Registra el café procesado de cada lote para poder venderlo.',
    desc: (f) => `el ingreso de ${num(f.quintales, 1)} quintales de ${f.lote_nombre}`,
    columnas: [
      { t: 'Fecha', k: 'fecha', f: fecha },
      { t: 'Lote', k: 'lote_nombre' },
      { t: 'Quintales', k: 'quintales', num: true, f: (v) => num(v, 2) },
    ],
    campos: [
      { k: 'lote_id', t: 'Lote', tipo: 'select', opciones: opcionesDe('/lotes', (l) => `${l.nombre} (${l.variedad})`) },
      { k: 'fecha', t: 'Fecha en que quedó en bodega', tipo: 'date', inicial: hoy },
      { k: 'quintales', t: 'Quintales de café procesado', tipo: 'number', paso: '0.1', min: 0.1 },
    ],
  },
  ventas: {
    titulo: 'Ventas de café', ruta: '/ventas', nuevo: 'Registrar venta', singular: 'venta', banner: true, guardado: 'Venta guardada.', eliminado: 'Venta eliminada.',
    buscarEn: 'comprador o fecha',
    vacio: 'Todavía no hay ventas. Registra la primera con «Nueva venta».',
    desc: (f) => `la venta a ${f.comprador} del ${fecha(f.fecha)}`,
    columnas: [
      { t: 'Fecha', k: 'fecha', f: fecha },
      { t: 'Comprador', k: 'comprador' },
      { t: 'Quintales', k: 'quintales', num: true, f: (v) => num(v, 2) },
      { t: 'Precio por quintal', k: 'precio_quintal', num: true, f: lempiras },
      { t: 'Total', k: 'total', num: true, f: lempiras },
    ],
    campos: [
      { k: 'fecha', t: 'Fecha', tipo: 'date', inicial: hoy },
      { k: 'comprador', t: 'Comprador', tipo: 'text', sugerencias: async () => [...new Set((await api('/ventas')).map((v) => v.comprador))] },
      { k: 'quintales', t: 'Quintales vendidos', tipo: 'number', paso: '0.1', min: 0.1, ayuda: 'No puedes vender más café del que hay en bodega.' },
      { k: 'precio_quintal', t: 'Precio por quintal (L)', tipo: 'number', paso: '1', min: 1 },
    ],
  },
};

const SECCIONES = [
  ['resumen', 'Resumen'], ['cosechas', 'Cosechas'], ['lotes', 'Lotes'], ['trabajadores', 'Trabajadores'],
  ['tarifas', 'Tarifas'], ['produccion', 'Café en bodega'], ['ventas', 'Ventas'], ['planilla', 'Planilla'],
];

/* ---------- Sesión ---------- */
function mostrarEntrada() {
  $('#app').hidden = true;
  $('#entrada').hidden = false;
  $('#formEntrada').usuario.focus();
}

function mostrarApp(nombre) {
  $('#entrada').hidden = true;
  $('#app').hidden = false;
  $('#nombreUsuario').textContent = nombre;
  irA(location.hash.slice(1) || 'resumen');
}

function cerrarSesion() {
  token = null;
  localStorage.removeItem('finca_token');
  mostrarEntrada();
}

$('#formEntrada').addEventListener('submit', async (e) => {
  e.preventDefault();
  const f = e.target, boton = f.querySelector('button'), error = $('#errorEntrada');
  error.hidden = true; boton.disabled = true;
  try {
    const r = await api('/auth/login', { metodo: 'POST', cuerpo: { usuario: f.usuario.value.trim(), password: f.password.value } });
    token = r.token;
    localStorage.setItem('finca_token', token);
    f.password.value = '';
    mostrarApp(r.nombre);
  } catch (err) {
    error.textContent = err.message; error.hidden = false;
  } finally { boton.disabled = false; }
});

$('#btnSalir').addEventListener('click', async () => {
  try { await api('/auth/logout', { metodo: 'POST' }); } catch (_) { /* ya estaba vencida */ }
  cerrarSesion();
});

/* ---------- Navegación ---------- */
$('#menu').innerHTML = SECCIONES.map(([id, t]) => `<button type="button" data-ir="${id}">${esc(t)}</button>`).join('');
$('#menu').addEventListener('click', (e) => { const b = e.target.closest('[data-ir]'); if (b) irA(b.dataset.ir); });

function irA(seccion) {
  if (!SECCIONES.some(([id]) => id === seccion)) seccion = 'resumen';
  location.hash = seccion;
  document.querySelectorAll('#menu button').forEach((b) => {
    if (b.dataset.ir === seccion) b.setAttribute('aria-current', 'page'); else b.removeAttribute('aria-current');
  });
  const vistas = { resumen: verResumen, planilla: verPlanilla };
  (vistas[seccion] || (() => verRecurso(seccion)))();
}

function encabezado(titulo, ...botones) {
  $('#titulo').textContent = titulo;
  const zona = $('#acciones');
  zona.innerHTML = '';
  botones.forEach(({ texto, clase = 'boton', alHacer }) => {
    const b = Object.assign(document.createElement('button'), { type: 'button', className: clase, textContent: texto });
    b.addEventListener('click', alHacer);
    zona.append(b);
  });
}

const errorEnVista = (e) => { $('#vista').innerHTML = `<p class="error" role="alert">${esc(e.message)}</p>`; };

/* ---------- Listados con CRUD ---------- */
let filas = [];

function verRecurso(clave) {
  const cfg = RECURSOS[clave];
  encabezado(cfg.titulo,
    { texto: 'Exportar CSV', alHacer: () => descargarCSV(clave, cfg.filtrosFecha ? { desde: $('#fDesde')?.value, hasta: $('#fHasta')?.value } : {}) },
    { texto: cfg.nuevo, clase: 'boton primario', alHacer: () => abrirFormulario(clave) });

  $('#vista').innerHTML = `
    ${cfg.banner ? '<div id="banner"></div>' : ''}
    <div class="barra">
      <label class="buscar">Buscar
        <input id="fBuscar" type="search" placeholder="Por ${esc(cfg.buscarEn)}">
      </label>
      ${cfg.filtrosFecha ? '<label>Desde<input id="fDesde" type="date"></label><label>Hasta<input id="fHasta" type="date"></label>' : ''}
    </div>
    <div id="tabla" class="panel"></div>`;

  let espera;
  $('#vista').querySelectorAll('input').forEach((i) =>
    i.addEventListener('input', () => { clearTimeout(espera); espera = setTimeout(() => cargarTabla(clave), 250); }));
  $('#tabla').addEventListener('click', (e) => {
    const b = e.target.closest('[data-accion]');
    if (!b) return;
    const fila = filas.find((f) => f.id === Number(b.dataset.id));
    if (b.dataset.accion === 'editar') abrirFormulario(clave, fila); else confirmarEliminar(clave, fila);
  });
  cargarTabla(clave);
}

async function pintarBodega() {
  try {
    const b = await api('/inventario');
    $('#banner').innerHTML = `<div class="cifras">
      <div class="cifra"><b>${num(b.disponible, 1)}</b><span>quintales en bodega, listos para vender</span></div>
      <div class="cifra"><b>${num(b.producido, 1)}</b><span>quintales producidos</span></div>
      <div class="cifra"><b>${num(b.vendido, 1)}</b><span>quintales vendidos</span></div></div>`;
  } catch (_) { /* el banner es informativo: si falla, la tabla sigue funcionando */ }
}

async function cargarTabla(clave) {
  const cfg = RECURSOS[clave], cont = $('#tabla');
  if (cfg.banner) pintarBodega();
  const q = new URLSearchParams();
  if ($('#fBuscar')?.value.trim()) q.set('buscar', $('#fBuscar').value.trim());
  if ($('#fDesde')?.value) q.set('desde', $('#fDesde').value);
  if ($('#fHasta')?.value) q.set('hasta', $('#fHasta').value);
  try {
    const consulta = q.toString();
    filas = await api(cfg.ruta + (consulta ? '?' + consulta : ''));
  } catch (e) { cont.innerHTML = `<p class="error">${esc(e.message)}</p>`; return; }

  if (!filas.length) {
    cont.innerHTML = `<p class="vacio">${q.toString() ? 'No hay resultados con esos filtros.' : esc(cfg.vacio)}</p>`;
    return;
  }
  const celda = (c, f) => `<td class="${c.num ? 'num' : ''}">${c.h ? c.h(f) : esc(c.f ? c.f(f[c.k], f) : f[c.k])}</td>`;
  cont.innerHTML = `<table>
    <thead><tr>${cfg.columnas.map((c) => `<th class="${c.num ? 'num' : ''}">${esc(c.t)}</th>`).join('')}<th></th></tr></thead>
    <tbody>${filas.map((f) => `<tr>${cfg.columnas.map((c) => celda(c, f)).join('')}
      <td><div class="celda-acciones">
        <button class="enlace" data-accion="editar" data-id="${f.id}">Editar</button>
        <button class="enlace rojo" data-accion="eliminar" data-id="${f.id}">Eliminar</button>
      </div></td></tr>`).join('')}</tbody></table>`;
}

/* ---------- Formularios y confirmación ---------- */
const dialogo = $('#dialogo');

async function abrirFormulario(clave, item = null) {
  const cfg = RECURSOS[clave];
  let controles;
  try {
    controles = await Promise.all(cfg.campos.map(async (c) => {
      const valor = item ? item[c.k] : (c.inicial ? c.inicial() : '');
      const ayuda = c.ayuda ? `<small>${esc(c.ayuda)}</small>` : '';
      if (c.tipo === 'select') {
        const ops = await c.opciones();
        return `<label>${esc(c.t)}<select name="${c.k}" required>
          <option value="" ${valor === '' ? 'selected' : ''} disabled>Elige una opción</option>
          ${ops.map(([id, t]) => `<option value="${id}" ${id === valor ? 'selected' : ''}>${esc(t)}</option>`).join('')}
        </select>${ayuda}</label>`;
      }
      let lista = '', atributoLista = '';
      if (c.sugerencias) {
        lista = `<datalist id="dl_${c.k}">${(await c.sugerencias()).map((x) => `<option value="${esc(x)}">`).join('')}</datalist>`;
        atributoLista = `list="dl_${c.k}"`;
      }
      const tipoHtml = c.tipo === 'int' || c.tipo === 'number' ? 'number' : c.tipo;
      const extra = [c.tipo === 'int' ? 'step="1"' : '', c.paso ? `step="${c.paso}"` : '', c.min != null ? `min="${c.min}"` : '',
        c.placeholder ? `placeholder="${esc(c.placeholder)}"` : '', atributoLista].join(' ');
      return `<label>${esc(c.t)}<input name="${c.k}" type="${tipoHtml}" value="${esc(valor)}" ${extra} required>${lista}${ayuda}</label>`;
    }));
  } catch (e) { aviso(e.message, 'mal'); return; }

  dialogo.innerHTML = `<form class="dialogo-caja" id="formRegistro">
    <h2>${item ? 'Editar' : 'Crear'} ${esc(cfg.singular || cfg.nuevo.replace(/^Nuev[oa] /, ''))}</h2>
    ${controles.join('')}
    <p class="error" id="errorForm" role="alert" hidden></p>
    <div class="dialogo-pie">
      <button type="button" class="boton" id="btnCancelar">Cancelar</button>
      <button type="submit" class="boton primario">Guardar</button>
    </div></form>`;
  $('#btnCancelar').addEventListener('click', () => dialogo.close());
  $('#formRegistro').addEventListener('submit', async (e) => {
    e.preventDefault();
    const datos = {}, error = $('#errorForm'), boton = e.target.querySelector('[type=submit]');
    cfg.campos.forEach((c) => {
      const v = e.target.elements[c.k].value;
      datos[c.k] = ['number', 'int', 'select'].includes(c.tipo) ? Number(v) : v.trim();
    });
    error.hidden = true; boton.disabled = true;
    try {
      await api(item ? `${cfg.ruta}/${item.id}` : cfg.ruta, { metodo: item ? 'PUT' : 'POST', cuerpo: datos });
      dialogo.close();
      aviso(cfg.guardado);
      cargarTabla(clave);
    } catch (err) {
      error.textContent = err.message; error.hidden = false;
    } finally { boton.disabled = false; }
  });
  if (!dialogo.open) dialogo.showModal();
}

function confirmarEliminar(clave, item) {
  const cfg = RECURSOS[clave];
  dialogo.innerHTML = `<div class="dialogo-caja">
    <h2>Eliminar ${esc(cfg.desc(item))}</h2>
    <p style="margin:0">Esta acción no se puede deshacer.</p>
    <p class="error" id="errorForm" role="alert" hidden></p>
    <div class="dialogo-pie">
      <button type="button" class="boton" id="btnCancelar">Cancelar</button>
      <button type="button" class="boton peligro" id="btnConfirmar">Eliminar</button>
    </div></div>`;
  $('#btnCancelar').addEventListener('click', () => dialogo.close());
  $('#btnConfirmar').addEventListener('click', async (e) => {
    e.target.disabled = true;
    try {
      await api(`${cfg.ruta}/${item.id}`, { metodo: 'DELETE' });
      dialogo.close();
      aviso(cfg.eliminado);
      cargarTabla(clave);
    } catch (err) {
      $('#errorForm').textContent = err.message; $('#errorForm').hidden = false; e.target.disabled = false;
    }
  });
  if (!dialogo.open) dialogo.showModal();
}

/* ---------- Barras ---------- */
function barras(items, { nombre, detalle = () => '', valor, maximo, texto, clase = '' }) {
  const tope = maximo ?? Math.max(...items.map(valor), 1);
  return `<ul class="barras">${items.map((i) => `<li>
    <span class="nombre" title="${esc(nombre(i))}">${esc(nombre(i))}<small>${esc(detalle(i))}</small></span>
    <span class="pista"><span class="relleno ${clase}" style="width:${(valor(i) / tope * 100).toFixed(1)}%"></span></span>
    <span class="valor">${texto(i)}</span></li>`).join('')}</ul>`;
}

/* ---------- Resumen ---------- */
async function verResumen() {
  encabezado('Resumen de la finca', { texto: 'Respaldar ahora', alHacer: respaldarAhora });
  $('#vista').innerHTML = '<p class="nota">Cargando…</p>';
  try {
    const [r, respaldos] = await Promise.all([api('/reportes/resumen'), api('/respaldos')]);
    const mesMax = Math.max(...r.latas_por_mes.map((m) => m.latas), 1);
    $('#vista').innerHTML = `
      <h2>La cosecha</h2>
      <div class="cifras">
        <div class="cifra"><b>${num(r.lotes)}</b><span>lotes en ${num(r.hectareas_total, 1)} hectáreas</span></div>
        <div class="cifra"><b>${num(r.trabajadores)}</b><span>cortadores registrados</span></div>
        <div class="cifra"><b>${num(r.latas_total)}</b><span>latas cosechadas</span></div>
        <div class="cifra"><b>${lempiras(r.pago_total)}</b><span>pagado en jornales</span></div>
      </div>
      <h2>El café y las ventas</h2>
      <div class="cifras">
        <div class="cifra"><b>${num(r.bodega.disponible, 1)}</b><span>quintales en bodega de ${num(r.bodega.producido, 1)} producidos</span></div>
        <div class="cifra"><b>${lempiras(r.ventas.monto)}</b><span>vendido en ${num(r.ventas.quintales, 1)} quintales</span></div>
        <div class="cifra"><b>${lempiras(r.utilidad_sobre_jornales)}</b><span>ventas menos jornales, sin otros gastos</span></div>
      </div>
      <div class="dos-columnas">
        <section class="bloque"><h2>Latas por mes</h2>
          ${r.latas_por_mes.length ? barras(r.latas_por_mes, { nombre: (m) => nombreMes(m.mes), valor: (m) => m.latas, maximo: mesMax, texto: (m) => num(m.latas), clase: 'mes' }) : '<p class="vacio">Aún no hay cosechas.</p>'}
        </section>
        <section class="bloque"><h2>Quiénes han cortado más latas</h2>
          ${r.top_cortadores.length ? barras(r.top_cortadores, { nombre: (t) => t.nombre, valor: (t) => t.latas, texto: (t) => num(t.latas), clase: 'mes' }) : '<p class="vacio">Aún no hay cosechas.</p>'}
        </section>
        <section class="bloque"><h2>Café producido por lote</h2>
          ${r.produccion_por_lote.some((l) => l.quintales) ? barras(r.produccion_por_lote, { nombre: (l) => l.nombre, detalle: (l) => `${l.variedad}, ${num(l.hectareas, 1)} ha`, valor: (l) => l.quintales_por_hectarea, texto: (l) => `${num(l.quintales, 1)} qq <small>${num(l.quintales_por_hectarea, 1)}/ha</small>` }) : '<p class="vacio">Aún no hay café en bodega.</p>'}
        </section>
        <section class="bloque"><h2>Ventas por comprador</h2>
          ${r.ventas.por_comprador.length ? `<table><thead><tr><th>Comprador</th><th class="num">Quintales</th><th class="num">Monto</th></tr></thead><tbody>
          ${r.ventas.por_comprador.map((c) => `<tr><td>${esc(c.comprador)}</td><td class="num">${num(c.quintales, 1)}</td><td class="num">${lempiras(c.monto)}</td></tr>`).join('')}
          </tbody></table>` : '<p class="vacio">Aún no hay ventas.</p>'}
        </section>
        <section class="bloque"><h2>Respaldos de la base</h2>
          <p class="nota">Se hace uno al encender la API y luego cada hora, en segundo plano.</p>
          <div id="listaRespaldos">${htmlRespaldos(respaldos)}</div>
        </section>
      </div>`;
  } catch (e) { errorEnVista(e); }
}

const htmlRespaldos = (lista) => lista.length
  ? `<table><tbody>${lista.slice(0, 5).map((x) => `<tr><td>${esc(x.archivo)}</td><td class="num">${num(x.kb, 1)} KB</td></tr>`).join('')}</tbody></table>`
  : '<p class="vacio">Todavía no hay respaldos.</p>';

async function respaldarAhora() {
  try {
    await api('/respaldos', { metodo: 'POST' });
    aviso('Respaldo iniciado en segundo plano.');
    setTimeout(async () => {
      const lista = $('#listaRespaldos');
      if (lista) lista.innerHTML = htmlRespaldos(await api('/respaldos'));
    }, 900);
  } catch (e) { aviso(e.message, 'mal'); }
}

/* ---------- Planilla y rendimiento ---------- */
function verPlanilla() {
  encabezado('Planilla y rendimiento por lote',
    { texto: 'Exportar planilla (CSV)', alHacer: () => descargarCSV('planilla', { desde: $('#pDesde').value, hasta: $('#pHasta').value }) });
  $('#vista').innerHTML = `
    <form id="formPlanilla" class="barra">
      <label>Desde<input id="pDesde" type="date" value="${haceDias(14)}" required></label>
      <label>Hasta<input id="pHasta" type="date" value="${hoy()}" required></label>
      <button class="boton primario" type="submit">Calcular</button>
    </form>
    <div id="resultado"></div>`;
  $('#formPlanilla').addEventListener('submit', (e) => { e.preventDefault(); calcularPlanilla(); });
  calcularPlanilla();
}

async function calcularPlanilla() {
  const cont = $('#resultado'), desde = $('#pDesde').value, hasta = $('#pHasta').value;
  cont.innerHTML = '<p class="nota">Calculando…</p>';
  try {
    const p = await api(`/planilla?desde=${desde}&hasta=${hasta}`);
    const aviso0 = p.cosechas_sin_tarifa
      ? `<p class="aviso-fila">${p.cosechas_sin_tarifa} cosechas de estas fechas no tienen tarifa vigente y no suman pago. Registra la tarifa en la sección Tarifas.</p>` : '';
    const tabla = p.trabajadores.length ? `<div class="panel"><table>
      <thead><tr><th>Trabajador</th><th>Identidad</th><th class="num">Días</th><th class="num">Latas</th><th class="num">Pago</th></tr></thead>
      <tbody>${p.trabajadores.map((t) => `<tr><td>${esc(t.nombre)}</td><td>${esc(t.identidad)}</td><td class="num">${t.dias}</td><td class="num">${num(t.latas)}</td><td class="num">${lempiras(t.pago)}</td></tr>`).join('')}
      <tr class="fila-total"><td colspan="3">Total de la planilla</td><td class="num">${num(p.total_latas)}</td><td class="num">${lempiras(p.total_pago)}</td></tr>
      </tbody></table></div>` : '<div class="panel"><p class="vacio">No hay cosechas entre esas fechas.</p></div>';
    const tope = Math.max(...p.rendimiento_lotes.map((l) => l.latas_por_hectarea), 1);
    cont.innerHTML = `${aviso0}${tabla}
      <section class="bloque rendimiento">
        <h2>Rendimiento por lote</h2>
        <p class="nota">Latas cosechadas por hectárea del ${fecha(p.desde)} al ${fecha(p.hasta)}. El lote de arriba es el que más rinde.</p>
        ${barras(p.rendimiento_lotes, {
          nombre: (l) => l.nombre, detalle: (l) => `${l.variedad}, ${num(l.hectareas, 1)} ha`,
          valor: (l) => l.latas_por_hectarea, maximo: tope,
          texto: (l) => `${num(l.latas_por_hectarea, 1)} <small>latas/ha</small>`,
        })}
      </section>`;
  } catch (e) { cont.innerHTML = `<p class="error" role="alert">${esc(e.message)}</p>`; }
}

/* ---------- Arranque ---------- */
(async function iniciar() {
  if (!token) return mostrarEntrada();
  try {
    const yo = await api('/auth/yo');
    mostrarApp(yo.nombre);
  } catch (_) { mostrarEntrada(); }
})();
