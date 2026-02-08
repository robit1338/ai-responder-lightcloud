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

import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from src.utils.provider_inference import ProviderResponseGenerator  # noqa: E402
from start.main import ConfigManager  # noqa: E402


def main():
    load_dotenv()
    config_manager = ConfigManager()
    prompt = "Привет! Расскажи коротко, как у тебя настроение."

    try:
        generator = ProviderResponseGenerator(config_manager)
    except Exception as exc:
        print(f"❌ Не удалось инициализировать провайдера: {exc}")
        return 1

    try:
        response = generator.generate_response(prompt)
    except Exception as exc:
        print(f"❌ Ошибка при запросе к провайдеру: {exc}")
        return 1

    print("✅ Ответ провайдера:")
    print(response)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
