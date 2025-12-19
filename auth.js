// auth.js - Gestión de Acceso y Registro de Personal

// 1. FUNCIÓN DE REGISTRO
document.getElementById('registerForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const email = document.getElementById('regEmail').value;
    const password = document.getElementById('regPass').value;
    const full_name = document.getElementById('regName').value;
    const hierarchy = document.getElementById('regHierarchy').value;

    // Registrar en Supabase Auth guardando jerarquía y nombre en metadata
    const { data, error } = await supabaseClient.auth.signUp({
        email: email,
        password: password,
        options: {
            data: {
                full_name: full_name,
                hierarchy: hierarchy
            }
        }
    });

    if (error) {
        alert("Error en el registro: " + error.message);
    } else {
        alert("¡Registro exitoso! Ya puede iniciar sesión.");
        // Volver al formulario de login
        toggleAuth(false); 
    }
});

// 2. FUNCIÓN DE INICIO DE SESIÓN (LOGIN)
document.getElementById('loginForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPass').value;

    const { data, error } = await supabaseClient.auth.signInWithPassword({
        email: email,
        password: password
    });

    if (error) {
        alert("Acceso denegado: " + error.message);
    } else {
        // Redirigir al panel operativo
        window.location.href = 'panel.html';
    }
});

// 3. PERSISTENCIA DE SESIÓN (Opcional pero recomendado)
// Si el usuario ya está logueado y entra al index.html, lo manda directo al panel
async function checkActiveSession() {
    const { data: { session } } = await supabaseClient.auth.getSession();
    if (session && window.location.pathname.includes('index.html')) {
        window.location.href = 'panel.html';
    }
}

checkActiveSession();