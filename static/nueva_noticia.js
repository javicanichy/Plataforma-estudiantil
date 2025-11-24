
document.addEventListener("DOMContentLoaded", () => {
    const autorId = localStorage.getItem("usuario_id");

    if (!autorId) {
        alert("Debes iniciar sesión para publicar noticias.");
        window.location.href = "/login";
        return;
    }

    // Colocar el ID dentro del campo hidden
    document.getElementById("autor_id").value = autorId;
});

