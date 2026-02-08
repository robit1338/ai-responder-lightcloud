# 🤖 AI Telegram Responder

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> Персональный Telegram-бот, который отвечает через облачную модель OpenRouter и имитирует стиль общения на основе истории переписки.

## 📋 Содержание

- [Описание](#-описание)
- [Возможности](#-возможности)
- [Технологии](#-технологии)
- [Быстрый старт](#-быстрый-старт)
- [Установка](#-установка)
- [Настройка](#-настройка)
- [Использование](#-использование)
- [Структура проекта](#-структура-проекта)
- [Режимы работы](#-режимы-работы)
- [Требования](#-требования)
- [Лицензия](#-лицензия)

## 📖 Описание

AI Telegram Responder — инструмент для автоматических ответов в Telegram через облачную модель OpenRouter, с имитацией стиля общения на основе истории переписки.

## ✨ Возможности

- Конвертация истории чатов Telegram в датасеты
- Имитация стиля общения на основе недавней переписки
- Настройка параметров генерации OpenRouter
- Несколько режимов работы (личные чаты, группы, "сталкер")
- Автоматические ответы в Telegram
- Анти-спам защита
- Удобная настройка через меню и конфиг-файлы

## 🛠️ Технологии

- Python 3.8+
- OpenRouter (HTTP API)
- Pyrogram

## ⚡ Быстрый старт

1. **Клонируйте репозиторий:**
   ```bash
   git clone https://github.com/username/ai-responder.git
   cd ai-responder
   ```

2. **Создайте виртуальное окружение и установите зависимости (Windows):**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Настройте Telegram API:**
   - Получите `api_id` и `api_hash` на [my.telegram.org](https://my.telegram.org/apps)
   - Заполните файл `.env` или `config/config.yaml` (см. ниже)

4. **Запустите приложение (Windows):**
   ```bash
   python start/windows/start_windows.py
   ```

## 📦 Установка

1. Клонируйте репозиторий и перейдите в папку проекта.
2. Создайте виртуальное окружение и активируйте его.
3. Установите зависимости из `requirements.txt`.


## ⚙️ Настройка

- **Через меню приложения:**  
  Запустите приложение и выберите пункт "3. Настройки" для конфигурирования режима работы бота.

- **Через файл `config/config.yaml`:**  
  Все основные параметры (`api_id`, `api_hash`, `phone`, `login`, `target_user_ids`, `target_channel_ids`, `mode`, `openrouter` и др.) настраиваются в этом файле.
  ```yaml
  telegram:
    api_id: ваш_api_id
    api_hash: ваш_api_hash
    phone: '+79001234567'
    login: ваш_логин
    target_user_ids: [123456789]
    target_channel_ids: [-1001234567890]
    mode: only_channel_messages
  ```
- **Через `.env`:**  
  Можно использовать переменные окружения для чувствительных данных (пример в `.env.example`).

## 🚀 Использование

### Основное меню

1. Конвертировать JSON в датасет
2. Запустить Telegram-бота
3. Настройки
4. Выход

### Пример запуска

```bash
python start/windows/start_windows.py
```

## 📁 Структура проекта

```
ai-responder/
├── src/
│   ├── bot/
│   └── utils/
├── start/
│   ├── main.py
│   └── windows/
├── config/
│   ├── config.yaml
│   └── config.json
├── .env
└── README.md
```

## 🔄 Режимы работы

- **only_private_chats** — ответы только в личных чатах
- **only_channel_messages** — ответы только в группах/каналах
- **stalker** — ответы определённым пользователям в любых чатах

## 📋 Требования

- Python 3.8+
- 4 ГБ RAM+
- API доступ к Telegram

## 📝 Конфигурация

- Все параметры хранятся в `config/config.yaml` (основные настройки, профили генерации, режимы и др.).
- Для чувствительных данных используйте `.env`.

## 📄 Лицензия

Проект распространяется под лицензией MIT. Подробнее — в файле [LICENSE](LICENSE).
