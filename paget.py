import os
import sys
import urllib.request
import time
from pathlib import Path
import requests 
import json
import tarfile
import subprocess
import shutil


GREEN    = "\033[38;5;41m"    # Яркий зелёный акцент Fluent
DARK_G   = "\033[38;5;28m"    # Глубокий хвойный зелёный
RED      = "\033[38;5;196m"   # Критическая ошибка (Красный)
YELLOW   = "\033[38;5;214m"   # Предупреждение / Статус (Жёлтый)
WHITE    = "\033[38;5;255m"   # Чистый белый текст
GRAY     = "\033[38;5;242m"   # Серый для второстепенного текста
RESET    = "\033[0m"          # Сброс цветов

VERSION = 1.0

def draw_progressbar(percent, width=40):
    """Рисует ползущий прогресс-бар в строку терминала"""
    filled_width = int(width * percent / 100)
    bar = f"{WHITE}{'█' * filled_width}{GRAY}{'▒' * (width - filled_width)}{RESET}"
    sys.stdout.write(f"\r    [{bar}] {WHITE}{percent:3d}%{RESET}")
    sys.stdout.flush()

def download_progress_hook(block_count, block_size, total_size):
    """Хук для подсчета процентов скачивания"""
    if total_size <= 0:
        return
        
    downloaded = block_count * block_size
    percent = int(downloaded * 100 / total_size)
    
    if percent > 100: 
        percent = 100
        
    draw_progressbar(percent)

def download_with_progress(url, destination):
    """Скачивает файл с прогресс-баром"""
    print(f"{YELLOW}[*] Process: {RESET}Downloading {url}...")
    
    urllib.request.urlretrieve(url, destination, download_progress_hook)
    print()
    print(f"{GREEN}[✓] Successfully: {RESET}File saved to {destination}")

def extract_tar_gz(archive_path, extract_to):
    """Распаковывает .tar.gz без вложенной папки"""
    extract_to = Path(extract_to)
    extract_to.mkdir(parents=True, exist_ok=True)
    
    print(f"{YELLOW}[*] Process: {RESET}Extracting {archive_path.name}...")
    
    try:
        with tarfile.open(archive_path, 'r:gz') as tar:
            # Получаем список всех файлов в архиве
            members = tar.getmembers()
            
            # Убираем первый уровень (если папка одна)
            if len(members) > 0:
                # Находим общий префикс (корневую папку)
                root_prefix = members[0].name.split('/')[0]
                all_in_root = all(m.name.startswith(root_prefix + '/') for m in members[1:])
                
                if all_in_root:
                    # Распаковываем, убирая префикс
                    for member in members:
                        # Убираем корневую папку из пути
                        new_name = '/'.join(member.name.split('/')[1:])
                        if new_name:
                            member.name = new_name
                            tar.extract(member, extract_to)
                else:
                    # Если структура сложная, просто распаковываем
                    tar.extractall(extract_to)
            
        print(f"{GREEN}[✓] Successfully: {RESET}Extracted to {extract_to}")
        return True
    except Exception as e:
        print(f"{RED}[!] Error: {RESET}{str(e)}")
        return False

def download_and_extract_package(url, package_name):
    """Скачивает и распаковывает пакет"""
    filename = url.split('/')[-1]
    tmp_path = Path("/tmp/paget/")
    download_path = tmp_path / filename
    extract_dir = tmp_path / package_name

    tmp_path.mkdir(exist_ok=True)
    
    print(f"{YELLOW}[*] Process: {RESET}Processing package: {package_name}")
    
    

    try:
        download_with_progress(url, download_path)
    except Exception as e:
        print(f"{RED}[!] Error: {RESET}Download failed: {e}")
        return None
    
    if extract_tar_gz(download_path, extract_dir):
        # Удаляем архив
        download_path.unlink()
        print(f"{GREEN}[✓] Successfully: {RESET}Temporary archive removed")
        return extract_dir
    else:
        return None

def remove_packet(packet):
    ...

def download_packet(packet_to_install):
    app_id = packet_to_install.lower()

    if os.getuid() == 0:
        bin_folder = Path("/usr/local/bin")
        share_folder = Path(f"/usr/local/share/")
        apps_folder = Path("/usr/local/share/applications")
        lshare_folder = Path.home() / ".local/share"

        lshare_folder.mkdir(parents=True, exist_ok=True)
    else:
        print(f"{RED}[!] Error: {RESET}This action requires {GREEN}SuperUser{RESET} rights{RESET}")
        return

    print(f"{YELLOW}[*] Process: {RESET}Searching for a package...{RESET}")
    

    try:
        packages_list = json.loads(requests.get("https://raw.githubusercontent.com/topdatop01/paget/refs/heads/packages/packages.json").content)
    except requests.exceptions.ConnectionError:
        print(f"{RED}[!] Error: {RESET}Internet connection error{RESET}")
        return
    
    if not app_id in packages_list["packages"]:
        print(f"{RED}[!] Error: {RESET}Package not found!{RESET}")

    print(f"{GREEN}[✓] Successfully: {RESET}Package found{RESET}")

    metadatas = share_folder / "paget/metadata"
    metadatas.mkdir(755, parents=True, exist_ok=True)

    app_data = packages_list["packages"][app_id]
    instaled = metadatas / (app_id + ".json")
    instaled = instaled.is_file()

    to_download = [[app_data["package_url"], app_id, instaled]]
    req_list = {}

    def collect_all_dependencies(pkg_name, packages_list, visited=None, to_download=None, req_list=None):
        if visited is None:
            visited = set()
        if to_download is None:
            to_download = []
        if req_list is None:
            req_list = {}
        
        # Защита от циклов
        if pkg_name in visited:
            return to_download, req_list
        
        visited.add(pkg_name)
        
        # Получаем данные пакета
        pkg_data = packages_list["packages"].get(pkg_name)
        if not pkg_data:
            return to_download, req_list
        
        # Проверяем, установлен ли
        is_installed = (metadatas / f"{pkg_name}.json").is_file()

        if is_installed:

        
        # Добавляем пакет, если его ещё нет
        if not any(pkg[1] == pkg_name for pkg in to_download):
            to_download.append([pkg_data["package_url"], pkg_name, is_installed])
        
        # Обновляем версию
        version = pkg_data.get("version", "1.0")
        if pkg_name not in req_list or req_list[pkg_name] < version:
            req_list[pkg_name] = version
        
        # Обрабатываем зависимости (рекурсивно)
        for dep_name, dep_version in pkg_data.get("requirements", {}).items():
            # Обновляем версию зависимости
            if dep_name not in req_list or req_list[dep_name] < dep_version:
                req_list[dep_name] = dep_version
            
            # Рекурсивный вызов
            collect_all_dependencies(dep_name, packages_list, visited, to_download, req_list)
        
        return to_download, req_list
    
    to_download, req_list = collect_all_dependencies(app_id, packages_list)

    print("\n------------------ PACKAGES ---------------------\n")

    for i in to_download:
        print(f"    {"[INSTALED]" if i[2] == True else ("[UPDATE]" if i[2] == 2 else "")}{packages_list["packages"][i[1]]["display_name"]} - {packages_list["packages"][i[1]]["version"]}")

    print()

    while True:
        a = input("Download packages? (y/n): ")
        if a == "y":
            break
        elif a == "n":
            quit()

    for i in to_download:
        if i[2] == True:
            print(f"{GREEN}[✓] Successfully: {RESET}{package_data["display_name"]} already installed!{RESET}")

        if i[2] == 2:
            

        files = download_and_extract_package(i[0], i[1])

        if files != None:
            print(f"{YELLOW}[*] Process: {RESET}Giving permisions...{RESET}")

            package_data = packages_list["packages"][i[1]]

            for v in package_data["chmod"]:
                file = files / v
                perms = package_data["chmod"][v]
                if isinstance(perms, str):
                    perms_num = int(perms, 8)
                else:
                    perms_num = int(str(perms), 8)
                os.chmod(file, perms_num)

            files_bin = files / "bin"
            files_share = files / "share"
            files_lshare = files / "local_share"
            files_apps = files / "applications"

            metadata = {
                "sys_name": i[1],
                "dispay_name": package_data["display_name"],
                "description": package_data["description"],
                "version": package_data["version"],
                "files": {
                    "bin_files": [],
                    "share_files": [],
                    "lshare_files": [],
                    "apps_files": []
                }
            }

            print(f"{YELLOW}[*] Process: {RESET}Install...{RESET}")

            print(f"{YELLOW}[*] Process: {RESET}Move to share...{RESET}")
            if files_share.is_dir():
                for v in files_share.rglob("*"):
                    shutil.move(str(v), str(share_folder))
                    metadata["files"]["share_files"].append(str(v))

            print(f"{YELLOW}[*] Process: {RESET}Move to bin...{RESET}")
            if files_bin.is_dir():
                for v in files_bin.rglob("*"):
                    shutil.move(str(v), str(bin_folder))
                    metadata["files"]["bin_files"].append(str(v))

            print(f"{YELLOW}[*] Process: {RESET}Move to aplications...{RESET}")
            if files_apps.is_dir():
                for v in files_apps.rglob("*"):
                    shutil.move(str(v), str(apps_folder))
                    metadata["files"]["apps_files"].append(str(v))

            print(f"{YELLOW}[*] Process: {RESET}Move to local share...{RESET}")
            if files_lshare.is_dir():
                for v in files_lshare.rglob("*"):
                    shutil.move(str(v), str(lshare_folder))
                    metadata["files"]["lshare_files"].append(str(v))

            print(f"{YELLOW}[*] Process: {RESET}Make metadata...{RESET}")

            metadataf = metadatas / f"{i[1]}.json"
            metadataf.touch(755, exist_ok=True)

            with open(str(metadataf), "w", encoding="utf-8") as file:
                json.dump(metadata, file)

            print(f"{GREEN}[✓] Successfully: {RESET}{package_data["display_name"]} successfully instaled!{RESET}")

def compile_packages(type_of, args):
    for package in args:
        if type_of == "install":
            download_packet(package)
        elif type_of == "remove":
            remove_packet()
        elif type_of == "update"

def show_help():
    """Выводит справочную информацию"""
    print(f"\n{GREEN}=== PAGET PACKAGE MANAGER: HELP ==={RESET}")
    print(f"Usage: {GREEN}paget [command] [arguments]{RESET}\n")
    print(f"Available commands:")
    print(f"  {GREEN}install [package]{RESET} - Download and install the program")
    print(f"   {GREEN}remove [package] {RESET}- Completely remove the program")
    print(f"   {GREEN}search [query] {RESET}  - Find a program in the repository")
    print(f"     {GREEN}list {RESET}          - Display a list of installed programs")
    print(f"   {GREEN}update {RESET}          - Update the package manager `paget`")
    print(f"     {GREEN}help {RESET}          - Show this menu\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"{RED}[!] Error: {RESET}There are no arguments!{RESET}")
        print(f"Type: {GREEN}paget help {RESET}to view available commands.{RESET}")
        sys.exit(0)

    # Забираем команду и переводим в нижний регистр
    action = sys.argv[1].lower()

    # 2. Вызовы одиночных команд (help, list)
    if action in ["help", "-h", "--help"]:
        show_help()
        
    elif action in ["list"]:
        list_packages()

    # 3. Вызовы команд, которые ТРЕБУЮТ второй аргумент (пакет / запрос)
    elif action in ["install", "remove", "search"]:
        # Проверяем, ввёл ли юзер аргумент для команды
        if len(sys.argv) < 3:
            print(f"{RED}[!] Error:{WHITE} An argument must be specified for the '{action}' command!\nType: {GREEN}paget {action} (package){RESET}")
            sys.exit(1)
            
        # Забираем сам аргумент (имя пакета или поисковый запрос)
        argument = sys.argv[2:]

        # Направляем аргумент в нужную функцию
        if action == "install":
            compile_packages("install", argument)
        elif action == "remove":
            compile_packages("remove", argument)
        elif action == "search":
            compile_packages("search", argument)

    elif action == "update":
        if len(sys.argv) < 3:
            compile_packages("update", ["all"])
        else:
            argument = sys.argv[2:]
            compile_packages("update", argument)

    # 4. Обработка неизвестного ввода
    else:
        print(f"{RED}[!] Error:{WHITE} Non-existent command: '{action}'{RESET}")
        print(f"Type: {GREEN}paget help{WHITE} to view available commands.{RESET}")
        sys.exit(1)
