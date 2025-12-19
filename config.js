// config.js
const supabaseUrl = 'https://ykplgqbtimhynjbyrsgx.supabase.co'; 
// Usando la llave anon public visible en tu captura de pantalla
const supabaseKey ='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlrcGxncWJ0aW1oeW5qYnlyc2d4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjYxNTM1NDksImV4cCI6MjA4MTcyOTU0OX0.qNeIyAql6dm780IQAP8AhUmFsVbNB1fmggVJe1QOhFE'; // Asegúrate de que esta sea la ANON KEY y no la SERVICE ROLE

// Cambiamos el nombre a supabaseClient para que no choque con la librería
const supabaseClient = supabase.createClient(supabaseUrl, supabaseKey);

// Lo publicamos globalmente para que auth.js y script.js lo vean
window.supabaseClient = supabaseClient;