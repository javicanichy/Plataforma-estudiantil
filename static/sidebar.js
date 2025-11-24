document.addEventListener("DOMContentLoaded", () => {

    const btnSidebar = document.getElementById("btn-sidebar");
    const sidebar = document.getElementById("sidebar");
    const btnClose = document.getElementById("btn-close-sidebar");
    const overlay = document.getElementById("sidebar-overlay");

    // Abrir sidebar
    btnSidebar.addEventListener("click", () => {
        sidebar.style.transform = "translateX(0)";
        overlay.style.display = "block";
        overlay.style.background = "rgba(0,0,0,0.3)";

        // Ocultar botón del menú cuando el sidebar está abierto
        btnSidebar.style.opacity = "0";
        btnSidebar.style.pointerEvents = "none";   // Evita clics invisibles
    });

    // Cerrar sidebar
    function cerrarSidebar() {
        sidebar.style.transform = "translateX(-100%)";
        overlay.style.background = "rgba(0,0,0,0)";

        // Mostrar el botón del menú otra vez
        setTimeout(() => {
            overlay.style.display = "none";
            btnSidebar.style.opacity = "1";
            btnSidebar.style.pointerEvents = "auto";
        }, 300); // coincide con la animación del CSS
    }

    // Botón de cerrar
    btnClose.addEventListener("click", cerrarSidebar);

    // Overlay para cerrar
    overlay.addEventListener("click", cerrarSidebar);
});
