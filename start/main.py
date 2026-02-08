# MIT License
#
# Copyright (c) 2025 Eiztrips
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import yaml
import asyncio
import tkinter as tk
from tkinter import filedialog
from typing import Dict, Any

from src.utils.data_processor import DataProcessor
from src.bot.telegram_client import TelegramResponder

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
YAML_CONFIG_FILE = os.path.join(BASE_DIR, 'config', 'config.yaml')

class ConfigManager:

    def __init__(self):
        self.config = {}
        self.yaml_config = self._load_yaml_config()

    def _load_yaml_config(self) -> Dict[str, Any]:
        if os.path.exists(YAML_CONFIG_FILE):
            try:
                with open(YAML_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                print(f"Ошибка загрузки YAML конфигурации: {e}")
        return {}

    def save_yaml_config(self):
        os.makedirs(os.path.dirname(YAML_CONFIG_FILE), exist_ok=True)
        try:
            with open(YAML_CONFIG_FILE, 'w', encoding='utf-8') as f:
                yaml.dump(self.yaml_config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            print(f"✅ Конфигурация успешно сохранена в {YAML_CONFIG_FILE}")
            return True
        except Exception as e:
            print(f"❌ Не удалось сохранить YAML конфигурацию: {e}")
            return False

    def get(self, section: str, key: str, default: Any = None) -> Any:
        try:
            if section in self.yaml_config and key in self.yaml_config[section]:
                return self.yaml_config[section][key]
            return default
        except Exception:
            return default

    def get_section(self, section: str, default: Any = None) -> Any:
        return self.yaml_config.get(section, default)

    def get_app_config(self, key: str, default: Any = None) -> Any:
        return self.yaml_config.get('main_settings', {}).get(key, default)

    def set_app_config(self, key: str, value: Any):
        if 'main_settings' not in self.yaml_config:
            self.yaml_config['main_settings'] = {}
        self.yaml_config['main_settings'][key] = value
        self.save_yaml_config()

    def get_telegram_config(self) -> Dict[str, Any]:
        return self.yaml_config.get('telegram', {})
    
    def get_data_processor_config(self) -> Dict[str, Any]:
        return self.yaml_config.get('data_processor', {})
    
    def get_full_config(self) -> Dict[str, Any]:
        return self.yaml_config

    def update_yaml_setting(self, section: str, key: str, value: Any):
        if section not in self.yaml_config:
            self.yaml_config[section] = {}
        self.yaml_config[section][key] = value

        if section != 'main_settings':
            if 'main_settings' not in self.yaml_config:
                self.yaml_config['main_settings'] = {}

            mapping = {
                'telegram': {'mode': 'telegram_mode'},
                'main_settings': {}
            }
            
            if section in mapping and key in mapping[section]:
                main_key = mapping[section][key]
                self.yaml_config['main_settings'][main_key] = value


def select_json_file():
    root = tk.Tk()
    root.withdraw()
    root.wm_attributes('-topmost', 1)
    root.update()
    file_path = filedialog.askopenfilename(
        title="Выберите JSON файл",
        filetypes=[("JSON files", "*.json")]
    )
    root.destroy()
    return file_path if file_path else None


def change_bot_mode(config_manager: ConfigManager):
    telegram_config = config_manager.get_telegram_config()
    current_mode = telegram_config.get('mode', 'only_private_chats')
    mode_descriptions = telegram_config.get('mode_descriptions', {})

    print("\n===== Изменение режима работы бота =====")
    print(f"Текущий режим: {current_mode}")
    print("\nДоступные режимы:")
    
    modes = list(mode_descriptions.items())
    for i, (mode, description) in enumerate(modes, 1):
        print(f"{i}. {mode} - {description}")

    choice = input("\nВыберите режим (1-{}) или 0 для отмены: ".format(len(modes)))

    if choice.isdigit() and 1 <= int(choice) <= len(modes):
        mode_idx = int(choice) - 1
        new_mode = modes[mode_idx][0]
        print(f"\n✅ Режим успешно изменен на: {new_mode} (измените config.yaml для сохранения)")
        return True
    elif choice == "0":
        print("Изменение режима отменено.")
        return False
    else:
        print("Неверный выбор.")
        return False


def settings_menu(config_manager: ConfigManager):
    """Меню настроек с улучшенной читаемостью и функционалом сохранения."""
    while True:
        print("\n" + "="*40)
        print("        НАСТРОЙКИ AI-RESPONDER")
        print("="*40)
        print("1. Режим Telegram-бота")
        print("2. Файлы поведения")
        print("3. Провайдер модели")
        print("4. Сохранить все настройки")
        print("5. Вернуться в главное меню")
        print("="*40)
        
        choice = input("Выберите опцию (1-5): ")

        if choice == "1":
            _handle_telegram_mode_settings(config_manager)
        elif choice == "2":
            _handle_behavior_files_settings(config_manager)
        elif choice == "3":
            _handle_provider_settings(config_manager)
        elif choice == "4":
            if config_manager.save_yaml_config():
                print("\n✅ Все настройки успешно сохранены в файл конфигурации!")
            else:
                print("\n❌ Не удалось сохранить настройки. Проверьте права доступа к файлу.")
        elif choice == "5":
            if _prompt_for_save_if_needed(config_manager):
                config_manager.save_yaml_config()
            break
        else:
            print("❌ Неверный выбор. Пожалуйста, введите число от 1 до 5.")


def _handle_telegram_mode_settings(config_manager: ConfigManager):
    print("\n" + "-"*40)
    print("     НАСТРОЙКА РЕЖИМА TELEGRAM БОТА")
    print("-"*40)
    
    yaml_cfg = config_manager.yaml_config
    telegram_cfg = yaml_cfg.get("telegram", {})
    mode_descriptions = telegram_cfg.get("mode_descriptions", {})

    current_mode = yaml_cfg.get("main_settings", {}).get("telegram_mode") \
        or telegram_cfg.get("mode", "only_private_chats")
    
    print(f"Текущий режим: {current_mode}")
    print("\nДоступные режимы:")
    
    modes = list(mode_descriptions.items())
    for i, (mode, description) in enumerate(modes, 1):
        current = "✓" if mode == current_mode else " "
        print(f"{i}. [{current}] {mode}")
        print(f"   {description}")
    
    choice_mode = input("\nВыберите режим (1-{}) или 0 для отмены: ".format(len(modes)))
    
    if choice_mode.isdigit() and 1 <= int(choice_mode) <= len(modes):
        mode_idx = int(choice_mode) - 1
        new_mode = modes[mode_idx][0]

        config_manager.update_yaml_setting('telegram', 'mode', new_mode)
        print(f"\n✅ Режим успешно изменен на: {new_mode}")
    elif choice_mode == "0":
        print("Изменение режима отменено.")
    else:
        print("❌ Неверный выбор.")


def _handle_behavior_files_settings(config_manager: ConfigManager):
    print("\n" + "-"*40)
    print("     ФАЙЛЫ ПОВЕДЕНИЯ")
    print("-"*40)

    llm_cfg = config_manager.yaml_config.get("llm", {})
    profile_cfg = llm_cfg.get("behavior_profile", {})
    behavior_dir = profile_cfg.get("behavior_files_dir", "data/behavior")

    if not os.path.exists(behavior_dir):
        os.makedirs(behavior_dir, exist_ok=True)

    files = [f for f in os.listdir(behavior_dir) if f.lower().endswith(".txt")]
    if not files:
        print(f"❌ В папке {behavior_dir} нет файлов .txt. Добавьте файл поведения и повторите.")
        return

    selected = profile_cfg.get("behavior_files", [])
    print(f"Текущие файлы: {', '.join(selected) if selected else 'не выбраны'}")
    print("\nДоступные файлы:")
    for i, filename in enumerate(files, 1):
        marker = "✓" if filename in selected else " "
        print(f"{i}. [{marker}] {filename}")

    choice = input("\nВыберите файл (номер) или 0 для отмены: ").strip()
    if choice == "0":
        print("Изменение отменено.")
        return
    if not choice.isdigit() or not (1 <= int(choice) <= len(files)):
        print("❌ Неверный выбор.")
        return

    filename = files[int(choice) - 1]
    config_manager.update_yaml_setting("llm", "behavior_profile", {
        **profile_cfg,
        "behavior_files": [filename],
    })
    print(f"\n✅ Подключен файл поведения: {filename}")


def _handle_provider_settings(config_manager: ConfigManager):
    print("\n" + "-"*40)
    print("     ПРОВАЙДЕР МОДЕЛИ")
    print("-"*40)

    llm_cfg = config_manager.yaml_config.get("llm", {})
    providers_cfg = config_manager.yaml_config.get("providers", {})
    providers = list(providers_cfg.keys())

    if not providers:
        print("❌ Провайдеры не настроены в config.yaml.")
        return

    current = llm_cfg.get("provider", providers[0])
    print(f"Текущий провайдер: {current}")
    print("\nДоступные провайдеры:")
    for i, name in enumerate(providers, 1):
        marker = "✓" if name == current else " "
        print(f"{i}. [{marker}] {name}")

    choice = input("\nВыберите провайдера (номер) или 0 для отмены: ").strip()
    if choice == "0":
        print("Изменение отменено.")
        return
    if not choice.isdigit() or not (1 <= int(choice) <= len(providers)):
        print("❌ Неверный выбор.")
        return

    selected = providers[int(choice) - 1]
    config_manager.update_yaml_setting("llm", "provider", selected)
    print(f"\n✅ Провайдер изменен на: {selected}")


def _prompt_for_save_if_needed(config_manager: ConfigManager) -> bool:
    response = input("\nСохранить изменения в файл конфигурации? (д/н): ")
    return response.lower() in ['д', 'y', 'yes', 'да']


def display_menu():
    print("\n" + "="*40)
    print("          AI-RESPONDER")
    print("="*40)
    print("1. Конвертировать JSON в датасет")
    print("2. Запустить Telegram-бота")
    print("3. Настройки")
    print("4. Выход")
    print("="*40)
    return input("Выберите опцию (1-4): ")

async def main():
    config_manager = ConfigManager()
    data_processor = DataProcessor(config_manager)

    while True:
        choice = display_menu()

        if choice == "1":
            print("\nВыберите JSON файл для конвертации в датасет")

            json_file_path = select_json_file()

            if not json_file_path:
                print("Выбор файла отменен")
                continue

            print(f"Выбран файл: {json_file_path}")

            output_name = input("Введите имя для выходного файла (оставьте пустым для автоматической генерации): ")
            output_name = output_name.strip() if output_name.strip() else None

            result = data_processor.parse_json_to_dataset(json_file_path, output_name)

            if result:
                print(f"Датасет успешно создан в форматах CSV и JSONL")
                print(f"CSV: {result['csv']['path']}")
                print(f"JSONL: {result['jsonl']['path']}")
            else:
                print("Ошибка при создании датасета")

        elif choice == "2":
            print("Запуск Telegram клиента...")

            try:
                responder = TelegramResponder(config_manager)
                try:
                    await responder.start()
                except ValueError as e:
                    print(f"\n❌ Ошибка конфигурации: {e}")
                    print("Проверьте config.yaml.")
                except KeyboardInterrupt:
                    print("\n⚠️ Остановка клиента...")
                    await responder.stop()
                    print("Клиент остановлен")
                except Exception as e:
                    print(f"\n❌ Ошибка при работе клиента: {e}")
                    if hasattr(responder, "stop"):
                        await responder.stop()

            except Exception as e:
                print(f"\n❌ Не удалось запустить Telegram клиент: {e}")

        elif choice == "3":
            settings_menu(config_manager)

        elif choice == "4":
            print("Выход из программы...")
            break

        else:
            print("Неверный выбор. Пожалуйста, выберите 1-4")


if __name__ == "__main__":
    asyncio.run(main())
