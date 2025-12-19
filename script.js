class GuardReportSystem {
    constructor() {
        this.records = [];
        this.currentUser = null;
        this.init();
    }

    async init() {
        const { data: { session } } = await supabase.auth.getSession();
        if (!session) {
            window.location.href = 'login.html';
            return;
        }
        
        this.currentUser = session.user;
        this.displayWelcome();
        this.setDefaultDateTime();
        
        document.getElementById('guardForm').addEventListener('submit', (e) => {
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
        const formData = new FormData(document.getElementById('guardForm'));
        const meta = this.currentUser.user_metadata;

        const { error } = await supabase.from('reportes').insert([{
            jerarquia: meta.hierarchy,
            nombre: meta.full_name,
            fecha_entrada: formData.get('entryDate'),
            hora_entrada: formData.get('entryTime'),
            user_id: this.currentUser.id
        }]);

        if (error) alert("Error al guardar registro");
        else {
            alert("¡Registro guardado!");
            await this.loadRecords();
        }
    }

    async loadRecords() {
        const { data } = await supabase.from('reportes').select('*').order('created_at', { ascending: false });
        this.records = data || [];
        this.render();
    }

    render() {
        const tbody = document.getElementById('recordsBody');
        tbody.innerHTML = this.records.map(r => `
            <tr>
                <td style="color:#d32f2f; font-weight:bold;">${r.jerarquia}</td>
                <td>${r.nombre}</td>
                <td>${r.fecha_entrada} | ${r.hora_entrada}</td>
                <td>
                    <button onclick="delRec('${r.id}')" style="color:#666; border:none; background:none; cursor:pointer;">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }

    exportPDF() {
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF();
        doc.setFillColor(211, 47, 47);
        doc.rect(0, 0, 210, 30, 'F');
        doc.setTextColor(255);
        doc.setFontSize(16);
        doc.text("BOMBEROS DE VALENCIA - REPORTE DE GUARDIA", 105, 20, { align: "center" });
        
        doc.autoTable({
            startY: 35,
            head: [['RANGO', 'PERSONAL', 'ENTRADA']],
            body: this.records.map(r => [r.jerarquia, r.nombre, `${r.fecha_entrada} ${r.hora_entrada}`]),
            headStyles: { fillColor: [26, 26, 26] },
            theme: 'striped'
        });
        doc.save(`Guardia_${new Date().toISOString().split('T')[0]}.pdf`);
    }
}

const system = new GuardReportSystem();
function exportToPDF() { system.exportPDF(); }
async function logout() { await supabase.auth.signOut(); window.location.href = 'login.html'; }
async function delRec(id) { 
    if(confirm("¿Eliminar registro?")) {
        await supabase.from('reportes').delete().eq('id', id);
        system.loadRecords();
    } 
}
function toggleRankEdit() { document.getElementById('rankEditForm').classList.toggle('hidden'); }

async function updateUserHierarchy() {
    const newRank = document.getElementById('newHierarchy').value;
    const { error } = await supabase.auth.updateUser({ data: { hierarchy: newRank } });
    if (error) alert("Error: " + error.message);
    else { alert("Rango actualizado."); location.reload(); }
}