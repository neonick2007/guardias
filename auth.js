// auth.js

// REGISTRO DE BOMBEROS
document.getElementById('registerForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('regEmail').value;
    const password = document.getElementById('regPass').value;
    const nombre = document.getElementById('regName').value;
    const jerarquia = document.getElementById('regHierarchy').value;

    const { data, error } = await supabaseClient.auth.signUp({
        email,
        password,
        options: {
            data: { full_name: nombre, hierarchy: jerarquia }
        }
    });

    if (error) {
        alert("Error: " + error.message);
    } else {
        alert("¡Cuenta creada con éxito! Ahora puedes iniciar sesión.");
        toggleAuth(false); // Regresa a la vista de login
    }
});

// INICIO DE SESIÓN
document.getElementById('loginForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPass').value;

    const { data, error } = await supabaseClient.auth.signInWithPassword({
        email,
        password
    });

    if (error) {
        alert("Error de acceso: " + error.message);
    } else {
        // Redirige al panel de reportes
        window.location.href = 'panel.html';
    }
});