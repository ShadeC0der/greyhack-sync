# greyhack-sync

Extrae una carpeta del sistema de archivos virtual de [Grey Hack](https://store.steampowered.com/app/605230/Grey_Hack/) y la replica localmente. Útil para respaldar scripts y notas. Los binarios del juego no se agregan

## Requisitos

- Python 3
- Grey Hack instalado via Steam

## Configuración

El script detecta automáticamente la base de datos del juego buscando en las rutas estándar de Steam según el sistema operativo. Solo necesitas crear el config si quieres sobrescribir algo.

**Ubicación del config:**

- Linux: `~/.config/greyhack-sync/config.conf`
- Windows: `%APPDATA%\greyhack-sync\config.conf`

```ini
[paths]

# Opcional: solo si el script no encuentra la DB automáticamente.
# Buscar en: Steam > Ajustes > Almacenamiento
# Linux:   <steam_library>/steamapps/common/Grey Hack/Grey Hack_Data/GreyHackDB.db
# Windows: <steam_library>\steamapps\common\Grey Hack\Grey Hack_Data\GreyHackDB.db
# db_path = /ruta/a/GreyHackDB.db

# Carpeta real donde se guardarán los archivos extraídos
output_dir = /ruta/de/salida

# Nombre exacto de la carpeta dentro del juego
target_folder = Mis-Cosas
```

## Uso

Agrega el alias a tu shell y recárgalo:

**zsh**

```bash
echo 'alias ghsync="$HOME/Proyectos/greyhack-sync/greyhack-sync.py"' >> ~/.zshrc
source ~/.zshrc
```

**bash**

```bash
echo 'alias ghsync="$HOME/Proyectos/greyhack-sync/greyhack-sync.py"' >> ~/.bashrc
source ~/.bashrc
```

**fish**

```bash
echo 'alias ghsync="$HOME/Proyectos/greyhack-sync/greyhack-sync.py"' >> ~/.config/fish/config.fish
source ~/.config/fish/config.fish
```

Luego ejecuta con:

```bash
ghsync
```

## Archivos

| Archivo                               | Descripción                    |
| ------------------------------------- | ------------------------------ |
| `greyhack-sync.py`                    | Script principal (compartible) |
| `~/.config/greyhack-sync/config.conf` | Rutas privadas, solo en tu PC  |
