import os
import sys
import urllib.request
import time
from pathlib import Path
import requests 
import json


GREEN    = "\033[38;5;41m"    # Яркий зелёный акцент Fluent
DARK_G   = "\033[38;5;28m"    # Глубокий хвойный зелёный
RED      = "\033[38;5;196m"   # Критическая ошибка (Красный)
YELLOW   = "\033[38;5;214m"   # Предупреждение / Статус (Жёлтый)
WHITE    = "\033[38;5;255m"   # Чистый белый текст
GRAY     = "\033[38;5;242m"   # Серый для второстепенного текста
RESET    = "\033[0m"          # Сброс цветов

def draw_progressbar(percent, width=40):
    """Рисует ползущий прогресс-бар в строку терминала"""
    filled_width = int(width * percent / 100)
    bar = f"{WHITE}{'█' * filled_width}{GRAY}{'▒' * (width - filled_width)}{RESET}"
    sys.stdout.write(f"\r    [{bar}] {WHITE}{percent:3d}%{RESET}")
    sys.stdout.flush()

def download_progress_hook(block_count, block_size, total_size):
    """
    Автоматический хук для подсчета процентов скачивания.
    block_count: сколько блоков уже прилетело
    block_size: размер одного блока данных
    total_size: общий размер файла в байтах
    """
    # Если сервер не отдал размер файла (total_size == -1), ставим заглушку
    if total_size <= 0:
        return
        
    downloaded = block_count * block_size
    percent = int(downloaded * 100 / total_size)
    
    if percent > 100: 
        percent = 100
        
    draw_progressbar(percent)

def download_packet(packet_to_install):
    app_id = packet_to_install.lower().replace(' ', '_')

    if os.getuid() == 0:
        bin_folder = Path("/usr/local/bin")
        share_folder = Path(f"/usr/local/share/{app_id}")
        apps_folder = Path("/usr/local/share/applications")
    else:
        print(f"{RED}[!] Error: {RESET}This action requires {GREEN}SuperUser{RESET} rights{RESET}")
        return

    print(f"{GREEN}[*] Process: {RESET}Searching for a package...{RESET}")
    
    try:
        packages_list = json.loads(requests.get("https://raw.githubusercontent.com/topdatop01/paget/refs/heads/packages/packages.json").content)
    except requests.exceptions.ConnectionError:
        print(f"{RED}[!] Error: {RESET}Internet connection error{RESET}")
        return
    
    if not app_id in packages_list["packages"]:
        print(f"{RED}[!] Error: {RESET}Package not found{RESET}")

    

def compile_packages(type_of, args):
    for package in args:
        if type_of == "install":
            download_packet(package)

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
            remove_package(argument)
        elif action == "search":
            search_package(argument)

    # 4. Обработка неизвестного ввода
    else:
        print(f"{RED}[!] Error:{WHITE} Non-existent command: '{action}'{RESET}")
        print(f"Type: {GREEN}paget help{WHITE} to view available commands.{RESET}")
        sys.exit(1)
