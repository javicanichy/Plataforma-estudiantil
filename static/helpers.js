// helpers.js
export const fetchJSON = async (url, options = {}) => {
  try {
    const res = await fetch(url, options);
    const data = await res.json().catch(() => null);
    return { ok: res.ok, status: res.status, data };
  } catch (err) {
    console.error("fetchJSON error:", err, url);
    return { ok: false, status: 0, data: null };
  }
};

export const mostrarMensaje = (el, texto, clase = '') => {
  if (!el) return;
  el.textContent = texto || '';
  el.className = clase;
};
