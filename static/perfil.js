document.addEventListener('DOMContentLoaded', function() {
    // Seleccionamos todas las fotos que Jinja renderizó
    const slides = document.querySelectorAll('.portada-slide');
    
    // Solo actuamos si hay más de una foto
    if (slides.length > 1) {
        let currentIndex = 0;

        // Forzamos el estilo inicial por si el CSS falló
        slides.forEach((img, i) => {
            img.style.position = 'absolute';
            img.style.top = '0';
            img.style.left = '0';
            img.style.display = (i === 0) ? 'block' : 'none';
        });

        // Iniciamos el intervalo de rotación
        setInterval(() => {
            // Ocultar la foto actual
            slides[currentIndex].style.display = 'none';
            
            // Calcular la siguiente (0, 1, 2 y vuelve a 0)
            currentIndex = (currentIndex + 1) % slides.length;
            
            // Mostrar la siguiente
            slides[currentIndex].style.display = 'block';
        }, 1000); // 1000ms = 1 segundo como tenías antes
    }
});