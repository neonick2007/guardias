class GuardReportSystem {
    constructor() {
        this.records = [];
        this.currentUser = null;
        this.init();
    }

    async init() {
        // Verificar si el usuario tiene una sesión activa
        const { data: { session } } = await supabase.auth.getSession();
        
        if (!session) {
            // Si no hay sesión, redirigir a la portada (que ahora es index.html)
            window.location.href = 'index.html';
            return;
        }
        
        this.currentUser = session.user;
        this.displayWelcome();
        this.setDefaultDateTime();
        
        // Escuchar el envío del formulario de guardia
        const guardForm = document.getElementById('guardForm');
        if (guardForm) {
            guardForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.addRecord();
            });
        }
        
        await this.loadRecords();
    }

    // Muestra el rango y nombre del bombero en el encabezado
    displayWelcome() {
        const meta = this.currentUser.user_metadata;
        const welcomeMsg = document.getElementById('welcome-message');
        if (welcomeMsg) {
            welcomeMsg.innerHTML = `<i class="fas fa-user-shield"></i> Bienvenido, ${meta.hierarchy} ${meta.full_name}`;
        }
    }

    // Coloca la fecha y hora actual automáticamente en el formulario
    setDefaultDateTime() {
        const now = new Date();
        const entryDate = document.getElementById('entryDate');
        const entryTime = document.getElementById('entryTime');
        
        if (entryDate) entryDate.value = now.toISOString().split('T')[0];
        if (entryTime) entryTime.value = now.toTimeString().slice(0, 5);
    }

    // Guarda el reporte en la base de datos de Supabase
    async addRecord() {
        const entryDate = document.getElementById('entryDate').value;
        const entryTime = document.getElementById('entryTime').value;
        const meta = this.currentUser.user_metadata;

        const { error } = await supabase.from('reportes').insert([{
            jerarquia: meta.hierarchy,
            nombre: meta.full_name,
            fecha_entrada: entryDate,
            hora_entrada: entryTime,
            user_id: this.currentUser.id
        }]);

        if (error) {
            alert("Error al guardar registro: " + error.message);
        } else {
            alert("¡Registro de guardia guardado con éxito!");
            await this.loadRecords();
        }
    }

    // Carga todos los registros de la tabla 'reportes'
    async loadRecords() {
        const { data, error } = await supabase
            .from('reportes')
            .select('*')
            .order('created_at', { ascending: false });

        if (error) {
            console.error("Error cargando registros:", error);
        } else {
            this.records = data || [];
            this.render();
        }
    }

    // Dibuja la tabla en el HTML
    render() {
        const tbody = document.getElementById('recordsBody');
        if (!tbody) return;

        tbody.innerHTML = this.records.map(r => `
            <tr>
                <td style="color:#d32f2f; font-weight:bold;">${r.jerarquia}</td>
                <td>${r.nombre}</td>
                <td>${r.fecha_entrada} | ${r.hora_entrada}</td>
                <td style="text-align: center;">
                    <button onclick="delRec('${r.id}')" style="color:#666; border:none; background:none; cursor:pointer;">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }

    // Genera el PDF con los datos actuales de la tabla
    exportPDF() {
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF();
        
        // Encabezado del PDF
        doc.setFillColor(211, 47, 47);
        doc.rect(0, 0, 210, 30, 'F');
        doc.setTextColor(255);
        doc.setFontSize(16);
        doc.text("BOMBEROS DE VALENCIA - REPORTE DE GUARDIA", 105, 20, { align: "center" });
        
        // Tabla del PDF
        doc.autoTable({
            startY: 35,
            head: [['RANGO', 'PERSONAL OPERATIVO', 'FECHA / HORA ENTRADA']],
            body: this.records.map(r => [r.jerarquia, r.nombre, `${r.fecha_entrada} ${r.hora_entrada}`]),
            headStyles: { fillColor: [26, 26, 26] },
            theme: 'striped'
        });

        doc.save(`Bitacora_Guardia_${new Date().toISOString().split('T')[0]}.pdf`);
    }
}

// INSTANCIA GLOBAL DEL SISTEMA
const system = new GuardReportSystem();

// FUNCIONES PARA LOS BOTONES DEL HTML
function exportToPDF() { 
    system.exportPDF(); 
}

async function logout() { 
    const { error } = await supabase.auth.signOut();
    if (error) alert("Error al salir");
    else window.location.href = 'index.html'; // Regresa al login
}

async function delRec(id) { 
    if(confirm("¿Seguro que desea eliminar este registro de la bitácora?")) {
        const { error } = await supabase.from('reportes').delete().eq('id', id);
        if (error) alert("No se pudo eliminar");
        else system.loadRecords();
    } 
}

// FUNCIONES PARA EL CAMBIO DE RANGO (ASCENSOS)
function toggleRankEdit() {
    const form = document.getElementById('rankEditForm');
    if (form) form.classList.toggle('hidden');
}

async function updateUserHierarchy() {
    const newRank = document.getElementById('newHierarchy').value;
    
    const { data, error } = await supabase.auth.updateUser({
        data: { hierarchy: newRank }
    });

    if (error) {
        alert("Error al actualizar rango: " + error.message);
    } else {
        alert("¡Felicitaciones! Rango actualizado a: " + newRank);
        location.reload(); // Recarga para actualizar el saludo y reportes futuros
    }
}