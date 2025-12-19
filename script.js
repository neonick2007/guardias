// script.js
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
            `<i class="fas fa-user-shield"></i> Bienvenido, ${meta.hierarchy} ${meta.full_name}`;
    }

    setDefaultDateTime() {
        const now = new Date();
        document.getElementById('entryDate').value = now.toISOString().split('T')[0];
        document.getElementById('entryTime').value = now.toTimeString().slice(0, 5);
    }

    async addRecord() {
        const entryDate = document.getElementById('entryDate').value;
        const entryTime = document.getElementById('entryTime').value;
        const meta = this.currentUser.user_metadata;

        const { error } = await supabaseClient.from('reportes').insert([{
            jerarquia: meta.hierarchy,
            nombre: meta.full_name,
            fecha_entrada: entryDate,
            hora_entrada: entryTime,
            user_id: this.currentUser.id
        }]);

        if (error) {
            alert("Error al guardar: " + error.message);
        } else {
            alert("¡Guardia registrada correctamente!");
            await this.loadRecords();
        }
    }

    async loadRecords() {
        const { data } = await supabaseClient
            .from('reportes')
            .select('*')
            .order('created_at', { ascending: false });
        this.records = data || [];
        this.render();
    }

    render() {
        const tbody = document.getElementById('recordsBody');
        if (!tbody) return;
        tbody.innerHTML = this.records.map(r => `
            <tr>
                <td style="color:#d32f2f; font-weight:bold;">${r.jerarquia}</td>
                <td>${r.nombre}</td>
                <td>${r.fecha_entrada} | ${r.hora_entrada}</td>
                <td>
                    <button onclick="delRec('${r.id}')" style="border:none; background:none; cursor:pointer; color:#666;">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }
}

const system = new GuardReportSystem();

async function logout() { 
    await supabaseClient.auth.signOut(); 
    window.location.href = 'index.html'; 
}

async function delRec(id) { 
    if(confirm("¿Desea eliminar este registro?")) {
        await supabaseClient.from('reportes').delete().eq('id', id);
        system.loadRecords();
    } 
}