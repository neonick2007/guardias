// script.js - Sistema de Gestión de Guardias
class GuardReportSystem {
    constructor() {
        this.records = [];
        this.currentUser = null;
        this.init();
    }

    async init() {
        const { data: { session } } = await supabaseClient.auth.getSession();
        if (!session) {
            window.location.href = 'index.html';
            return;
        }
        this.currentUser = session.user;
        this.displayWelcome();
        this.setDefaultDateTime();
        
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

        const { data, error } = await supabaseClient.from('reportes').insert([payload]).select();

        if (error) {
            alert("Error al guardar: " + error.message);
        } else {
            alert("✅ Registro guardado exitosamente.");
            document.getElementById('guardForm').reset();
            this.setDefaultDateTime();
            
            await this.loadRecords();

            if (data && data.length > 0) {
                sendWS(data[0].id);
            }
        }
    }

    async loadRecords() {
        const { data, error } = await supabaseClient
            .from('reportes')
            .select('*')
            .order('created_at', { ascending: false });
        
        if (error) return;
        this.records = data || [];
        this.render();
    }

    render() {
    const tbody = document.getElementById('recordsBody');
    if (!tbody) return;
    
    tbody.innerHTML = this.records.map(r => `
        <tr>
            <td>
                <strong>${r.jerarquia}</strong><br>
                ${r.nombre}
            </td>
            <td>
                <div style="line-height: 1.4;">
                    <strong><i class="fas fa-map-marker-alt"></i> ${r.estacion}</strong> - <small>SEC: "${r.seccion}"</small><br>
                    <span style="color: #555; font-size: 0.85rem;">
                        <i class="far fa-calendar-alt"></i> ${r.fecha_entrada} <br>
                        <i class="far fa-clock"></i> ${r.hora_entrada} HLV
                    </span>
                </div>
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

window.system = new GuardReportSystem();

async function sendWS(id) {
    let r = window.system.records.find(rec => rec.id === id);
    
    // Si no está en memoria, lo buscamos en la DB (Solución al error de reintento)
    if(!r) {
        const { data } = await supabaseClient.from('reportes').select('*').eq('id', id).single();
        r = data;
    }

    if(r) buildWhatsAppLink(r);
}

function buildWhatsAppLink(r) {
    // Separación lógica de Nombre y Apellido (Sin 's')
    const partes = r.nombre.trim().split(" ");
    const nombreIndividual = partes[0] || "";
    const apellidoIndividual = partes.slice(1).join(" ") || "";

    const mensaje = `🖋 *REPORTE DE ASISTENCIA A GUARDIA DE COLABORACIÓN* 🖋\n\n` +
        `📌 *ESTACION:* ${r.estacion}\n` +
        `📌 *JERARQUÍA:* ${r.jerarquia}\n` +
        `*NOMBRE:* ${nombreIndividual}\n` +
        `*APELLIDO:* ${apellidoIndividual}\n\n` +
        `📌 *FECHA ENTRADA:* ${r.fecha_entrada}\n` +
        `📌 *HORA ENTRADA:* ${r.hora_entrada} HLV\n\n` +
        `📌 *FECHA SALIDA:* ${r.fecha_salida}\n` +
        `📌 *HORA SALIDA:* ${r.hora_salida} HLV\n\n` +
        `📌 *SECCIÓN DE GUARDIA:* "${r.seccion}"\n` +
        `📌 *OBSERVACIONES:* ${r.observaciones}\n\n` +
        `▶️ _Oficial de Comando:_\n` +
        `▶️ _Oficial de los Servicios:_\n` +
        `▶️ _Jefe de Sección:_\n\n` +
        `🚨 *Disciplina y Abnegación*`;

    window.open(`https://wa.me/?text=${encodeURIComponent(mensaje)}`, '_blank');
}

async function logout() { 
    await supabaseClient.auth.signOut(); 
    window.location.href = 'index.html'; 
}

async function delRec(id) { 
    if(confirm("¿Seguro que desea eliminar este registro?")) {
        const { error } = await supabaseClient.from('reportes').delete().eq('id', id);
        if(!error) window.system.loadRecords();
    } 
}