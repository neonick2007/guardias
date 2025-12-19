// script.js
class GuardReportSystem {
    constructor() {
        this.records = [];
        this.currentUser = null;
        this.init();
    }

    async init() {
        // Verificar sesión de usuario en Supabase
        const { data: { session } } = await supabaseClient.auth.getSession();
        
        if (!session) {
            window.location.href = 'index.html';
            return;
        }
        
        this.currentUser = session.user;
        this.displayWelcome();
        this.setDefaultDateTime();
        
        // Escuchar el envío del formulario de guardia
        document.getElementById('guardForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.addRecord();
        });
        
        await this.loadRecords();
    }

    displayWelcome() {
        const meta = this.currentUser.user_metadata;
        document.getElementById('welcome-message').innerHTML = 
            `<i class="fas fa-user-shield"></i> ${meta.hierarchy} ${meta.full_name}`;
    }

    setDefaultDateTime() {
        const now = new Date();
        const tomorrow = new Date(now);
        tomorrow.setDate(tomorrow.getDate() + 1);

        // Formatear fechas para los inputs (YYYY-MM-DD)
        document.getElementById('entryDate').value = now.toISOString().split('T')[0];
        document.getElementById('entryTime').value = "08:00";
        
        document.getElementById('exitDate').value = tomorrow.toISOString().split('T')[0];
        document.getElementById('exitTime').value = "08:00";
    }

    async addRecord() {
        const meta = this.currentUser.user_metadata;
        const payload = {
            jerarquia: meta.hierarchy,
            nombre: meta.full_name,
            estacion: document.getElementById('estacion').value,
            seccion: document.getElementById('seccionGuardia').value,
            fecha_entrada: document.getElementById('entryDate').value,
            hora_entrada: document.getElementById('entryTime').value,
            fecha_salida: document.getElementById('exitDate').value,
            hora_salida: document.getElementById('exitTime').value,
            observaciones: document.getElementById('observaciones').value || "Sin novedades",
            user_id: this.currentUser.id
        };

        const { error } = await supabaseClient.from('reportes').insert([payload]);

        if (error) {
            alert("Error al guardar: " + error.message);
        } else {
            alert("✅ Registro guardado exitosamente.");
            document.getElementById('guardForm').reset();
            this.setDefaultDateTime();
            await this.loadRecords();
        }
    }

    async loadRecords() {
        const { data, error } = await supabaseClient
            .from('reportes')
            .select('*')
            .order('created_at', { ascending: false });
        
        if (error) {
            console.error("Error cargando datos:", error);
            return;
        }
        this.records = data || [];
        this.render();
    }

    render() {
        const tbody = document.getElementById('recordsBody');
        if (!tbody) return;
        
        tbody.innerHTML = this.records.map(r => `
            <tr>
                <td><strong>${r.jerarquia}</strong><br>${r.nombre}</td>
                <td>
                    <small><b>ESTACIÓN:</b></small> ${r.estacion}<br>
                    <small><b>SEC:</b></small> "${r.seccion}"<br>
                    <small><b>ENTRADA:</b> ${r.fecha_entrada} | ${r.hora_entrada}</small><br>
                    <small><b>SALIDA:</b> ${r.fecha_salida} | ${r.hora_salida}</small>
                </td>
                <td>
                    <button onclick="sendWS('${r.id}')" class="btn-ws">
                        <i class="fab fa-whatsapp"></i> Reporte
                    </button>
                </td>
                <td>
                    <button onclick="delRec('${r.id}')" style="color:#d32f2f; border:none; background:none; cursor:pointer; font-size:1.2em;">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }
}

// 1. CREAR LA INSTANCIA GLOBAL (Crucial para que el botón funcione)
window.system = new GuardReportSystem();

// 2. FUNCIÓN DE WHATSAPP GLOBAL
function sendWS(id) {
    // Busca los datos en la instancia global
    const r = window.system.records.find(rec => rec.id === id);
    
    if(!r) {
        alert("No se encontró la información del reporte.");
        return;
    }

    // Construcción del mensaje con saltos de línea y codificación segura
    const textoReporte = `🖋 *REPORTE DE ASISTENCIA A GUARDIA DE COLABORACIÓN* 🖋\n\n` +
        `▶️ _Estación:_ ${r.estacion}\n` +
        `▶️ _Jerarquía:_ ${r.jerarquia}\n` +
        `▶️ _Nombres:_ ${r.nombre}\n\n` +
        `▶️ _Fecha Entrada:_ ${r.fecha_entrada}\n` +
        `▶️ _Hora Entrada:_ ${r.hora_entrada} HLV\n\n` +
        `▶️ _Fecha Salida:_ ${r.fecha_salida}\n` +
        `▶️ _Hora Salida:_ ${r.hora_salida} HLV\n\n` +
        `▶️ _Sección de Guardia:_ "${r.seccion}"\n` +
        `▶️ _Observaciones:_ ${r.observaciones}\n\n` +
        `▶️ _Oficial de Comando:_ \n` +
        `▶️ _Oficial de los Servicios:_ \n` +
        `▶️ _Jefe de Sección:_ \n\n` +
        `🚨 *Disciplina y Abnegación*`;

    const url = `https://wa.me/?text=${encodeURIComponent(textoReporte)}`;
    window.open(url, '_blank');
}

// 3. FUNCIONES DE APOYO GLOBALES
async function logout() { 
    await supabaseClient.auth.signOut(); 
    window.location.href = 'index.html'; 
}

async function delRec(id) { 
    if(confirm("¿Seguro que desea eliminar este registro de la bitácora?")) {
        const { error } = await supabaseClient.from('reportes').delete().eq('id', id);
        if(!error) window.system.loadRecords();
    } 
}