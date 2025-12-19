# Sistema de Reportes de Guardia - Bomberos

Un sistema web completo para la gestión y generación de reportes de guardia del departamento de bomberos.

## 🚒 Características

- **Registro de Personal**: Captura de datos completos del personal en guardia
- **Gestión de Jerarquías**: Sistema de rangos desde Comandante hasta Cadete
- **Control de Horarios**: Registro de entrada y salida con cálculo automático de duración
- **Exportación de Reportes**: Generación de archivos PDF y Excel
- **Almacenamiento Local**: Persistencia de datos en el navegador
- **Interfaz Responsiva**: Diseño moderno y adaptable a diferentes dispositivos
- **Filtros y Búsqueda**: Herramientas para localizar registros específicos

## 📋 Datos Capturados

El sistema registra la siguiente información para cada miembro del personal:

- **Jerarquía**: Coronel, Teniente Coronel, Mayor, Capitán, Primer Teniente, Teniente, Sargento Mayor, Sargento Primero, Sargento, Cabo Primero, Cabo, Distinguido, Bombero
- **Nombre**: Nombre del personal
- **Apellidos**: Apellidos completos
- **Fecha de Entrada**: Día de inicio de la guardia
- **Hora de Entrada**: Hora exacta de inicio
- **Fecha de Salida**: Día de finalización de la guardia
- **Hora de Salida**: Hora exacta de finalización
- **Duración**: Cálculo automático del tiempo de servicio

## 🚀 Instalación y Uso

### Requisitos
- Navegador web moderno (Chrome, Firefox, Safari, Edge)
- Conexión a internet (para cargar las librerías externas)

### Instalación
1. Descarga todos los archivos del proyecto
2. Coloca los archivos en una carpeta
3. Abre el archivo `index.html` en tu navegador web

### Uso Básico

#### 1. Registrar Personal en Guardia
1. Completa el formulario en la sección "Registro de Personal"
2. Selecciona la jerarquía del personal
3. Ingresa nombre y apellidos
4. Establece fecha y hora de entrada
5. Opcionalmente, establece fecha y hora de salida
6. Haz clic en "Guardar Registro"

#### 2. Gestionar Registros
- **Editar**: Haz clic en el botón de edición (lápiz) en la tabla
- **Eliminar**: Haz clic en el botón de eliminación (basura) en la tabla
- **Buscar**: Usa el campo de búsqueda para filtrar por nombre o jerarquía
- **Filtrar**: Usa el menú desplegable para filtrar por jerarquía específica

#### 3. Exportar Reportes
- **PDF**: Haz clic en "Exportar PDF" para generar un reporte en formato PDF
- **Excel**: Haz clic en "Exportar Excel" para generar un archivo Excel

## 🎨 Características de la Interfaz

### Diseño Profesional
- Colores corporativos del departamento de bomberos
- Gradientes y efectos visuales modernos
- Iconos intuitivos de Font Awesome
- Animaciones suaves y transiciones

### Responsividad
- Adaptable a dispositivos móviles y tablets
- Diseño flexible que se ajusta a diferentes tamaños de pantalla
- Navegación optimizada para touch

### Jerarquías Visuales
- Badges de colores distintivos para cada jerarquía organizados por categorías:
  - **Oficiales Superiores**: Coronel, Teniente Coronel, Mayor (colores púrpura/rosa)
  - **Oficiales**: Capitán, Primer Teniente, Teniente (colores azul/verde)
  - **Suboficiales**: Sargento Mayor, Sargento Primero, Sargento (colores naranja/amarillo)
  - **Tropa**: Cabo Primero, Cabo, Distinguido, Bombero (colores marrón/rojo)
- Sistema de colores que refleja la importancia del rango
- Identificación visual rápida del personal

## 💾 Almacenamiento de Datos

El sistema utiliza **Local Storage** del navegador para:
- Persistir todos los registros entre sesiones
- Mantener la configuración del usuario
- Permitir trabajo offline

**Nota**: Los datos se almacenan localmente en el navegador. Para respaldo permanente, exporta regularmente los reportes.

## 🔧 Funcionalidades Técnicas

### Cálculo Automático de Duración
- Calcula automáticamente el tiempo de servicio
- Maneja cambios de día en las guardias
- Muestra "En servicio" para personal activo

### Validaciones
- Campos obligatorios marcados
- Validación de fechas y horarios
- Prevención de datos duplicados

### Exportación Avanzada
- **PDF**: Formato profesional con encabezados y tablas estructuradas
- **Excel**: Archivo compatible con Microsoft Excel y Google Sheets
- Nombres de archivo con fecha automática

## 📱 Compatibilidad

### Navegadores Soportados
- ✅ Google Chrome 80+
- ✅ Mozilla Firefox 75+
- ✅ Safari 13+
- ✅ Microsoft Edge 80+

### Dispositivos
- ✅ Computadoras de escritorio
- ✅ Laptops
- ✅ Tablets
- ✅ Smartphones

## 🛠️ Estructura del Proyecto

```
bomberos/
├── index.html          # Página principal
├── styles.css          # Estilos CSS
├── script.js           # Lógica JavaScript
└── README.md           # Documentación
```

## 📊 Ejemplo de Uso

### Escenario Típico
1. **Inicio de Guardia**: El comandante registra la entrada del personal a las 08:00
2. **Durante la Guardia**: Se pueden agregar más miembros del personal
3. **Finalización**: Se registran las salidas conforme el personal termina su turno
4. **Reporte**: Al final del día, se exporta un reporte completo en PDF

### Datos de Ejemplo
```
Jerarquía: Capitán
Nombre: Juan Carlos
Apellidos: Pérez González
Fecha Entrada: 2024-01-15
Hora Entrada: 08:00
Fecha Salida: 2024-01-15
Hora Salida: 16:00
Duración: 8h 0m
```

### Jerarquía Completa del Cuerpo de Bomberos
1. **Coronel** - Máximo rango
2. **Teniente Coronel** - Oficial superior
3. **Mayor** - Oficial superior
4. **Capitán** - Oficial
5. **Primer Teniente** - Oficial
6. **Teniente** - Oficial
7. **Sargento Mayor** - Suboficial
8. **Sargento Primero** - Suboficial
9. **Sargento** - Suboficial
10. **Cabo Primero** - Tropa
11. **Cabo** - Tropa
12. **Distinguido** - Tropa
13. **Bombero** - Tropa base

## 🔒 Seguridad y Privacidad

- Los datos se almacenan únicamente en el navegador local
- No se envían datos a servidores externos
- Control total sobre la información del departamento
- Cumplimiento con políticas de privacidad institucionales

## 🆘 Solución de Problemas

### Problemas Comunes

**Los datos no se guardan**
- Verifica que el navegador tenga habilitado Local Storage
- Asegúrate de no estar en modo incógnito

**No se pueden exportar archivos**
- Verifica que el navegador permita descargas
- Revisa que haya registros para exportar

**La interfaz no se ve correctamente**
- Actualiza el navegador a la versión más reciente
- Verifica la conexión a internet para cargar las librerías

### Contacto de Soporte
Para soporte técnico o reportar problemas, contacta al administrador del sistema.

## 📄 Licencia

Este sistema está desarrollado para uso interno del Departamento de Bomberos. Todos los derechos reservados.

---

**Desarrollado con ❤️ para el Departamento de Bomberos**

*Sistema de Reportes de Guardia v1.0*
