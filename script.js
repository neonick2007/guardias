// script.js
class GuardReportSystem {
    constructor() {
        this.records = [];
        this.currentUser = null;
        this.init();
    }

    async init() {
        // Verificar sesión de usuario
        const { data: { session } } = await supabaseClient.auth.getSession();
        
        if (!session) {
            window.location.href = 'index.html';
            return;
        }
        
        this.currentUser = session.user;
        this.displayWelcome();
        this.setDefaultDateTime();
        
        // Escuchar el envío del formulario
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

        // Fecha y hora actual para entrada
        document.getElementById('entryDate').value = now.toISOString().split('T')[0];
        document.getElementById('entryTime').value = "08:00";
        
        // Fecha de mañana y hora para salida
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

// Función global para generar WhatsApp (Cargos en blanco al final)
function sendWS(id) {
    const r = system.records.find(rec => rec.id === id);
    if(!r) return;

    const mensaje = `🖋 *REPORTE DE ASISTENCIA A GUARDIA DE COLABORACIÓN* 🖋%0A%0A` +
        `📌 *ESTACION:* ${r.estacion}%0A` +
        `📌 *JERARQUÍA:* ${r.jerarquia}%0A` +
        `*NOMBRES:* ${r.nombre}%0A%0A` +
        `📌 *ENTRADA:* ${r.fecha_entrada} | ${r.hora_entrada} HLV%0A` +
        `📌 *SALIDA:* ${r.fecha_salida} | ${r.hora_salida} HLV%0A` +
        `📌 *SECCIÓN DE GUARDIA:* "${r.seccion}"%0A` +
        `📌 *OBSERVACIONES:* ${r.observaciones}%0A%0A` +
        `▶️ _Oficial de Comando: _%0A` +
        `▶️ _Oficial de los Servicios: _%0A` +
        `▶️ _Jefe de Sección: _%0A%0A` +
        `🚨 *Disciplina y Abnegación*`;

    window.open(`https://wa.me/?text=${mensaje}`, '_blank');
}

const system = new GuardReportSystem();

async function logout() { 
    await supabaseClient.auth.signOut(); 
    window.location.href = 'index.html'; 
}

async function delRec(id) { 
    if(confirm("¿Seguro que desea eliminar este registro de la bitácora?")) {
        await supabaseClient.from('reportes').delete().eq('id', id);
        system.loadRecords();
    } 
}