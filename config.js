// config.js
const supabaseUrl = 'https://ykplgqbtimhynjbyrsgx.supabase.co'; // Tu URL de Supabase
const supabaseKey = 'sb_secret__5-noSoZJWzu0Z8IcmTEiQ_MSl4g4J4';           // Tu Anon Key

// Inicializamos el cliente de Supabase globalmente
const supabase = supabase.createClient(supabaseUrl, supabaseKey);