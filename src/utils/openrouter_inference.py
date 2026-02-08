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

import json
import logging
import os
import urllib.error
import urllib.request
from pathlib import Path

import yaml

BASE_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = BASE_DIR / "config" / "config.yaml"
DEFAULT_API_URL = "https://openrouter.ai/api/v1/chat/completions"


class BehaviorProfileManager:
    def __init__(self, config):
        profile_config = config.get("behavior_profile", {})
        self.messages_window = profile_config.get("messages_window", 100)
        self.update_every_messages = profile_config.get("update_every_messages", 50)
        self.storage_path = Path(profile_config.get("storage_path", "data/behavior_profile.txt"))
        self.meta_path = self.storage_path.with_suffix(self.storage_path.suffix + ".meta.json")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    def load_profile(self):
        if self.storage_path.exists():
            return self.storage_path.read_text(encoding="utf-8").strip()
        return ""

    def save_profile(self, profile_text):
        self.storage_path.write_text(profile_text.strip(), encoding="utf-8")

    def load_meta(self):
        if self.meta_path.exists():
            return json.loads(self.meta_path.read_text(encoding="utf-8"))
        return {"messages_seen": 0}

    def save_meta(self, meta):
        self.meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    def should_update(self, messages_seen):
        meta = self.load_meta()
        last_seen = meta.get("messages_seen", 0)
        return messages_seen - last_seen >= self.update_every_messages

    def record_messages_seen(self, messages_seen):
        meta = self.load_meta()
        meta["messages_seen"] = messages_seen
        self.save_meta(meta)


class OpenRouterResponseGenerator:
    def __init__(self, config_manager=None):
        if config_manager:
            self.config = config_manager.get_section("openrouter", {})
            logging_config = config_manager.get_section("logging", {})
        else:
            with CONFIG_PATH.open("r", encoding="utf-8") as handle:
                config = yaml.safe_load(handle)
            self.config = config.get("openrouter", {})
            logging_config = config.get("logging", {})

        logging.basicConfig(
            level=getattr(logging, logging_config.get("level", "INFO")),
            format=logging_config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
        )
        self.logger = logging.getLogger(__name__)
        self.api_url = self.config.get("api_url", DEFAULT_API_URL)
        self.api_key = self._resolve_api_key()
        self.model = self._resolve_model()
        self.site_url = self._resolve_site_url()
        self.app_name = self._resolve_app_name()
        self.generation = self.config.get("generation", {})
        self.profile_manager = BehaviorProfileManager(self.config)

        if not self.api_key:
            raise ValueError("OpenRouter API key is missing. Set OPENROUTER_API_KEY or config.openrouter.api_key.")

    def _resolve_api_key(self):
        env_key = self.config.get("api_key_env", "OPENROUTER_API_KEY")
        return os.getenv(env_key) or self.config.get("api_key", "")

    def _resolve_model(self):
        env_key = self.config.get("model_env", "OPENROUTER_MODEL")
        return os.getenv(env_key) or self.config.get("model", "meta-llama/llama-3.1-8b-instruct")

    def _resolve_site_url(self):
        env_key = self.config.get("site_url_env", "OPENROUTER_SITE_URL")
        return os.getenv(env_key) or self.config.get("site_url", "")

    def _resolve_app_name(self):
        env_key = self.config.get("app_name_env", "OPENROUTER_APP_NAME")
        return os.getenv(env_key) or self.config.get("app_name", "AI-Responder")

    def _build_system_prompt(self, behavior_profile):
        prompt_config = self.config.get("system_prompt", {})
        base = prompt_config.get("base", "").strip()
        rules = prompt_config.get("rules", [])
        rules_block = "\n".join(f"- {rule}" for rule in rules if rule)
        sections = [section for section in (base, "Правила:\n" + rules_block if rules_block else "") if section]
        if behavior_profile:
            sections.append("Профиль поведения:\n" + behavior_profile.strip())
        return "\n\n".join(sections).strip()

    def _prepare_messages(self, message, conversation_history=None, behavior_profile=""):
        system_prompt = self._build_system_prompt(behavior_profile)
        messages = [{"role": "system", "content": system_prompt}] if system_prompt else []
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": message})
        return messages

    def _post(self, payload):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.site_url:
            headers["HTTP-Referer"] = self.site_url
        if self.app_name:
            headers["X-Title"] = self.app_name
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(self.api_url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8")
            self.logger.error("OpenRouter API error: %s", detail)
            raise

    def generate_response(self, message, conversation_history=None, behavior_profile=None):
        profile_text = behavior_profile or self.profile_manager.load_profile()
        payload = {
            "model": self.model,
            "messages": self._prepare_messages(message, conversation_history, profile_text),
            "max_tokens": self.generation.get("max_tokens", 256),
            "temperature": self.generation.get("temperature", 0.8),
            "top_p": self.generation.get("top_p", 0.9),
        }
        response = self._post(payload)
        return response["choices"][0]["message"]["content"].strip()

    def analyze_behavior_profile(self, messages):
        if not messages:
            return ""
        prompt = (
            "Сделай краткий профиль поведения автора переписки: стиль, тон, типичные темы, "
            "манера отвечать. Пиши кратко, без списков действий."
        )
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": prompt}] + messages,
            "max_tokens": 256,
            "temperature": 0.4,
            "top_p": 0.9,
        }
        response = self._post(payload)
        return response["choices"][0]["message"]["content"].strip()

    def update_behavior_profile(self, messages, total_messages_seen):
        if not self.profile_manager.should_update(total_messages_seen):
            return self.profile_manager.load_profile()
        windowed = messages[-self.profile_manager.messages_window :]
        profile_text = self.analyze_behavior_profile(windowed)
        if profile_text:
            self.profile_manager.save_profile(profile_text)
            self.profile_manager.record_messages_seen(total_messages_seen)
        return profile_text
