#!/usr/bin/env python3
"""
Grey Hack - Sincronizador de archivos virtuales
Extrae una carpeta del juego y la replica en el sistema real.
Configuración en: ~/.config/greyhack-sync/config.conf
"""

import sqlite3
import json
import os
import sys
import configparser
from pathlib import Path

HOME = Path.home()

if sys.platform == "win32":
    CONFIG_PATH = Path(os.environ.get("APPDATA", HOME)) / "greyhack-sync/config.conf"
else:
    CONFIG_PATH = HOME / ".config/greyhack-sync/config.conf"


def find_db_automatically():
    """Busca la base de datos del juego según el sistema operativo."""
    if sys.platform == "win32":
        steam_roots = [
            Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "Steam",
            Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Steam",
        ]
    else:
        steam_roots = [
            HOME / ".local/share/Steam",
        ]

    db_relative = Path("steamapps/common/Grey Hack/Grey Hack_Data/GreyHackDB.db")

    # Buscar en la librería principal y librerías adicionales
    for root in steam_roots:
        candidate = root / db_relative
        if candidate.exists():
            return candidate

        # Revisar librerías adicionales en libraryfolders.vdf
        vdf = root / "steamapps/libraryfolders.vdf"
        if vdf.exists():
            for line in vdf.read_text(encoding="utf-8", errors="ignore").splitlines():
                if '"path"' in line:
                    extra = Path(line.split('"path"')[1].strip().strip('"'))
                    candidate = extra / db_relative
                    if candidate.exists():
                        return candidate

    return None


def load_config():
    cfg = configparser.ConfigParser()

    if CONFIG_PATH.exists():
        cfg.read(CONFIG_PATH, encoding="utf-8")

    db_path = cfg.get("paths", "db_path", fallback=None)
    output_dir = cfg.get("paths", "output_dir", fallback=None)
    target_folder = cfg.get("paths", "target_folder", fallback=None)

    # Auto-detectar db_path si no está en el config
    if not db_path:
        found = find_db_automatically()
        if found:
            print(f"  [auto] Base de datos encontrada en:\n    {found}\n")
            db_path = str(found)
        else:
            print(f"ERROR: No se pudo encontrar GreyHackDB.db automáticamente.")
            print(f"Especifica 'db_path' manualmente en:\n  {CONFIG_PATH}")
            exit(1)

    if not output_dir:
        print(f"ERROR: Falta 'output_dir' en:\n  {CONFIG_PATH}")
        exit(1)

    if not target_folder:
        print(f"ERROR: Falta 'target_folder' en:\n  {CONFIG_PATH}")
        exit(1)

    return {
        "db_path":       db_path,
        "output_dir":    output_dir,
        "target_folder": target_folder,
    }


def get_file_content(cursor, file_id):
    cursor.execute("SELECT Content FROM Files WHERE ID = ?", (file_id,))
    row = cursor.fetchone()
    return row[0] if row else ""


def collect_game_tree(cursor, folder_node, current_path, game_files, game_dirs, root_path):
    """Recorre el árbol del juego y registra archivos y carpetas esperados."""
    game_dirs.add(current_path)

    for f in folder_node.get("files", []):
        if f.get("isBinario"):
            print(f"  [binario omitido] {(current_path / f['nombre']).relative_to(root_path.parent)}")
            continue
        file_path = current_path / f["nombre"]
        content = get_file_content(cursor, f["ID"]) or ""
        game_files[file_path] = content

    for sub in folder_node.get("folders", []):
        collect_game_tree(cursor, sub, current_path / sub["nombre"], game_files, game_dirs, root_path)


def sync(game_files, game_dirs, output_dir):
    added = updated = deleted_files = deleted_dirs = unchanged = 0

    # Eliminar archivos que ya no existen en el juego
    for real_file in list(output_dir.rglob("*")):
        if real_file.is_file() and real_file not in game_files:
            real_file.unlink()
            print(f"  [eliminado] {real_file.relative_to(output_dir)}")
            deleted_files += 1

    # Eliminar carpetas vacías que ya no existen en el juego (de más profunda a menos)
    for real_dir in sorted(output_dir.rglob("*"), reverse=True):
        if real_dir.is_dir() and real_dir not in game_dirs and real_dir != output_dir:
            try:
                real_dir.rmdir()
                print(f"  [carpeta eliminada] {real_dir.relative_to(output_dir)}")
                deleted_dirs += 1
            except OSError:
                pass

    # Crear/actualizar archivos
    for file_path, content in game_files.items():
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if file_path.exists():
            if file_path.read_text(encoding="utf-8") == content:
                unchanged += 1
                continue
            file_path.write_text(content, encoding="utf-8")
            print(f"  [actualizado] {file_path.relative_to(output_dir)}")
            updated += 1
        else:
            file_path.write_text(content, encoding="utf-8")
            print(f"  [nuevo] {file_path.relative_to(output_dir)}")
            added += 1

    return added, updated, deleted_files, deleted_dirs, unchanged


def find_folder(node, name):
    if isinstance(node, dict):
        if node.get("nombre") == name:
            return node
        for v in node.values():
            result = find_folder(v, name)
            if result:
                return result
    elif isinstance(node, list):
        for item in node:
            result = find_folder(item, name)
            if result:
                return result
    return None


def main():
    cfg = load_config()
    db_path = cfg["db_path"]
    output_dir = Path(cfg["output_dir"])
    target_folder = cfg["target_folder"]

    if not os.path.exists(db_path):
        print(f"ERROR: No se encontró la base de datos en:\n  {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT FileSystem FROM Computer WHERE IsPlayer = 1")
    row = cursor.fetchone()
    if not row:
        print("ERROR: No se encontró el computador del jugador en la base de datos.")
        conn.close()
        return

    filesystem = json.loads(row[0])
    target = find_folder(filesystem, target_folder)

    if not target:
        print(f"ERROR: No se encontró la carpeta '{target_folder}' en el juego.")
        conn.close()
        return

    print(f"Sincronizando '{target_folder}' -> {output_dir}\n")

    game_files = {}
    game_dirs = set()
    root_path = output_dir / target_folder
    collect_game_tree(cursor, target, root_path, game_files, game_dirs, root_path)
    conn.close()

    added, updated, deleted_files, deleted_dirs, unchanged = sync(game_files, game_dirs, output_dir)

    print(f"\nResumen: {added} nuevos, {updated} actualizados, {deleted_files} eliminados, {unchanged} sin cambios")


if __name__ == "__main__":
    main()
