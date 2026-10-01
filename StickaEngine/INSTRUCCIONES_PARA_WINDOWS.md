# Instrucciones para Compilar StickaEngine en Windows

## Requisitos Previos

1. **Sistema Operativo**: Windows 10 o 11
2. **Python**: Versión 3.10 o superior (recomendado 3.12)
3. **Pip**: Gestor de paquetes de Python

## Paso 1: Clonar el Repositorio

```cmd
cd C:\
git clone https://github.com/elsenorperronbear/StickaEngine.git
cd StickaEngine\StickaEngine
```

## Paso 2: Crear Entorno Virtual (Opcional pero recomendado)

```cmd
python -m venv venv
venv\Scripts\activate
```

## Paso 3: Instalar Dependencias

```cmd
pip install -r requirements.txt
pip install pyinstaller pillow
```

Si no tienes el archivo `requirements.txt`, instala manualmente:
```cmd
pip install PyQt6==6.7.0 pillow==10.2.0 pyinstaller==6.22.0
```

## Paso 4: Crear Icono (Opcional)

El script de build creará un icono automáticamente si no existe. Pero puedes crear uno personalizado:

1. Crea un archivo `icon.ico` de 256x256 píxeles en la raíz del proyecto
2. O usa el script para generarlo automáticamente

## Paso 5: Compilar el Ejecutable

### Opción A: Usar el script de build automático

```cmd
python build_installer.py
```

Este script:
- Limpia builds anteriores
- Crea el icono si no existe
- Compila con PyInstaller
- Crea el acceso directo en el escritorio

### Opción B: Compilar manualmente con PyInstaller

```cmd
pyinstaller StickaEngine.spec --onefile --windowed
```

### Opción C: Compilar con NSIS Installer (Instalador Profesional)

1. Descarga e instala NSIS: https://nsis.sourceforge.io/Download
2. Compila el instalador:
```cmd
makensis installer.nsi
```

Esto creará `StickaEngine_Setup.exe` en la raíz del proyecto.

## Paso 6: Probar el Ejecutable

Después de compilar, el ejecutable estará en:
```
StickaEngine\dist\StickaEngine.exe
```

**Importante**: No ejecutes el script `main.py` directamente. Debes:
1. Primero instalar la aplicación usando el instalador o el script de build
2. Luego ejecutar el acceso directo del escritorio o el .exe compilado

## Paso 7: Crear Acceso Directo Manual (Opcional)

Si el script automático no funcionó, puedes crear el acceso directo manualmente:

```cmd
powershell -ExecutionPolicy Bypass -File create_shortcut.ps1
```

O manualmente:
1. Haz clic derecho en el escritorio
2. Nuevo > Acceso directo
3. Ubicación: `C:\ruta\al\proyecto\StickaEngine\dist\StickaEngine.exe`
4. Nombre: `StickaEngine`

## Solución de Problemas

### Error: "No module named PyQt6"

```cmd
pip install PyQt6==6.7.0
```

### Error: "PyInstaller not found"

```cmd
pip install pyinstaller
```

### Error: "Pillow not found"

```cmd
pip install pillow
```

### El ejecutable no se abre

1. Asegúrate de tener todas las dependencias instaladas
2. Verifica que el archivo `icon.ico` exista
3. Prueba a compilar sin `--onefile`:
```cmd
pyinstaller StickaEngine.spec --windowed
```

### Problemas con HiDPI

El código ya incluye soporte para HiDPI. Si los GIFs se ven pixelados:
1. Asegúrate de que tu sistema tenga la configuración de escala correcta
2. Verifica que el monitor esté configurado correctamente en Windows

## Estructura de Archivos

```
StickaEngine/
├── StickaEngine/
│   ├── main.py              # Código principal
│   ├── StickaEngine.spec    # Configuración de PyInstaller
│   ├── build_windows_exe.spec
│   ├── build_installer.py   # Script de build automático
│   ├── create_shortcut.ps1 # Script para crear acceso directo
│   ├── installer.nsi        # NSIS installer script
│   ├── license.txt          # Licencia MIT
│   └── requirements.txt     # Dependencias
├── dist/                   # Carpeta de salida (se crea al compilar)
└── build/                  # Archivos temporales de build
```

## Notas Adicionales

- **Tamaño del ejecutable**: El .exe final tendrá aproximadamente 20-30 MB
- **Tiempo de compilación**: Puede tardar varios minutos dependiendo de tu hardware
- **Pruebas**: Siempre prueba el ejecutable en una máquina limpia para asegurarte de que funciona
- **Actualizaciones**: El sistema de marketplace y auto-update funciona con GitHub Releases

## Desinstalar

1. Ejecuta el desinstalador desde el menú Inicio
2. O elimina manualmente:
   - `C:\Users\<tu_usuario>\AppData\Local\StickaEngine`
   - El acceso directo del escritorio

---

**Versión**: 1.0.0  
**Fecha**: 2024  
**Autor**: StickaEngine Team
