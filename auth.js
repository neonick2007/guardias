// Manejador del Formulario de Registro
document.getElementById('registerForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Captura de datos de los inputs
    const email = document.getElementById('regEmail').value;
    const password = document.getElementById('regPass').value;
    const nombre = document.getElementById('regName').value;
    const jerarquia = document.getElementById('regHierarchy').value;

    // Proceso de registro en Supabase
    const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
            // Guardamos nombre y rango en la metadata del usuario
            data: { 
                full_name: nombre, 
                hierarchy: jerarquia 
            }
        }
    });

    if (error) {
        alert("Error en el registro: " + error.message);
        console.error("Detalle del error:", error);
    } else {
        // Mensaje de éxito
        alert("¡Cuenta creada con éxito! Bienvenido al sistema.");
        
        // Si desactivaste 'Confirm Email' en Supabase, el usuario ya puede loguearse
        // Limpiamos el formulario y volvemos a la vista de login
        document.getElementById('registerForm').reset();
        if (typeof toggleAuth === 'function') {
            toggleAuth(false); // Función definida en el index.html
        } else {
            location.reload(); 
        }
    }
});

// Manejador del Formulario de Inicio de Sesión (Login)
document.getElementById('loginForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPass').value;

    // Intento de conexión
    const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password
    });

    if (error) {
        // Si el error es "Email not confirmed", es porque falta apagarlo en Supabase
        if (error.message.includes("Email not confirmed")) {
            alert("Error: Debes confirmar tu correo o desactivar la confirmación en Supabase.");
        } else {
            alert("Credenciales incorrectas: " + error.message);
        }
        console.error("Login error:", error);
    } else {
        // ÉXITO: Redirigir al panel de guardias
        console.log("Sesión iniciada:", data.user);
        window.location.href = 'panel.html';
    }
});