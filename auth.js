// Dentro del evento de loginForm
const { error } = await supabase.auth.signInWithPassword({ email, password });

if (error) {
    alert("Error: " + error.message);
} else {
    // CAMBIO: Ahora enviamos a panel.html
    window.location.href = 'panel.html'; 
}