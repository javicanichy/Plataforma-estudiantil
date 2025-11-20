export function initSidebar() {
    document.addEventListener('click', function(e) {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebar-overlay');
        const btn = document.getElementById('btn-sidebar');
        const btnClose = document.getElementById('btn-close-sidebar');

        if (!sidebar || !overlay || !btn || !btnClose) return;

        // Click en botón abrir
        if (e.target === btn) {
            sidebar.style.transform = 'translateX(0)';
            overlay.style.display = 'block';
            btn.style.opacity = '0';
            btn.style.pointerEvents = 'none';
        }

        // Click en botón cerrar o overlay
        if (e.target === btnClose || e.target === overlay) {
            sidebar.style.transform = 'translateX(-100%)';
            overlay.style.display = 'none';
            btn.style.opacity = '1';
            btn.style.pointerEvents = 'auto';
        }

        // Click en cualquier enlace dentro del sidebar
        if (sidebar.contains(e.target) && e.target.tagName === 'A') {
            sidebar.style.transform = 'translateX(-100%)';
            overlay.style.display = 'none';
            btn.style.opacity = '1';
            btn.style.pointerEvents = 'auto';
        }
    });
}
