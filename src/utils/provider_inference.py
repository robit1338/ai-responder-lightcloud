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
import urllib.parse
import urllib.request
from pathlib import Path

import yaml

BASE_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = BASE_DIR / "config" / "config.yaml"
DEFAULT_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_GOOGLE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


class BehaviorProfileManager:
    def __init__(self, config):
        profile_config = config.get("behavior_profile", {})
        self.messages_window = profile_config.get("messages_window", 100)
        self.update_every_messages = profile_config.get("update_every_messages", 50)
        self.storage_path = Path(profile_config.get("storage_path", "data/behavior_profile.txt"))
        self.behavior_files_dir = Path(profile_config.get("behavior_files_dir", "data/behavior"))
        self.behavior_files = profile_config.get("behavior_files", [])
        self.meta_path = self.storage_path.with_suffix(self.storage_path.suffix + ".meta.json")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.behavior_files_dir.mkdir(parents=True, exist_ok=True)

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

    def load_behavior_files(self):
        contents = []
        for entry in self.behavior_files:
            path = Path(entry)
            if not path.is_absolute():
                path = self.behavior_files_dir / entry
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8").strip()
            if text:
                contents.append(text)
        return "\n\n".join(contents).strip()


class ProviderResponseGenerator:
    def __init__(self, config_manager=None):
        if config_manager:
            full_config = config_manager.get_full_config()
            logging_config = config_manager.get_section("logging", {})
        else:
            with CONFIG_PATH.open("r", encoding="utf-8") as handle:
                full_config = yaml.safe_load(handle)
            logging_config = full_config.get("logging", {})

        self.llm_config = full_config.get("llm", {})
        self.providers_config = full_config.get("providers", {})
        self.provider = self.llm_config.get("provider", "openrouter")
        self.provider_config = self.providers_config.get(self.provider, {})

        logging.basicConfig(
            level=getattr(logging, logging_config.get("level", "INFO")),
            format=logging_config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
        )
        self.logger = logging.getLogger(__name__)
        self.generation = self.llm_config.get("generation", {})
        self.profile_manager = BehaviorProfileManager(self.llm_config)

        self.api_url = self._resolve_api_url()
        self.api_key = self._resolve_api_key()
        self.model = self._resolve_model()
        self.site_url = self._resolve_optional("site_url_env", "site_url", "")
        self.app_name = self._resolve_optional("app_name_env", "app_name", "AI-Responder")

        if not self.api_key:
            raise ValueError(
                f"{self.provider} API key is missing. "
                f"Set {self.provider.upper()}_API_KEY or config.providers.{self.provider}.api_key."
            )

    def _resolve_api_url(self):
        if self.provider == "google":
            return self.provider_config.get("api_url", DEFAULT_GOOGLE_URL)
        return self.provider_config.get("api_url", DEFAULT_OPENROUTER_URL)

    def _resolve_optional(self, env_key_name, config_key, fallback):
        env_key = self.provider_config.get(env_key_name)
        if env_key:
            value = os.getenv(env_key)
            if value:
                return value
        return self.provider_config.get(config_key, fallback)

    def _resolve_api_key(self):
        env_key = self.provider_config.get("api_key_env", f"{self.provider.upper()}_API_KEY")
        return os.getenv(env_key) or self.provider_config.get("api_key", "")

    def _resolve_model(self):
        env_key = self.provider_config.get("model_env", f"{self.provider.upper()}_MODEL")
        return os.getenv(env_key) or self.provider_config.get("model", "")

    def _build_system_prompt(self, behavior_profile):
        prompt_config = self.llm_config.get("system_prompt", {})
        base = prompt_config.get("base", "").strip()
        rules = prompt_config.get("rules", [])
        rules_block = "\n".join(f"- {rule}" for rule in rules if rule)
        sections = [section for section in (base, "Правила:\n" + rules_block if rules_block else "") if section]
        behavior_files = self.profile_manager.load_behavior_files()
        if behavior_files:
            sections.append("Файлы поведения:\n" + behavior_files)
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

    def _post_openrouter(self, payload):
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

    def _post_google(self, payload):
        query = urllib.parse.urlencode({"key": self.api_key})
        url = f"{self.api_url}/{self.model}:generateContent?{query}"
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8")
            self.logger.error("Google API error: %s", detail)
            raise

    def _call_provider(self, messages):
        if self.provider == "google":
            system_prompt = ""
            if messages and messages[0]["role"] == "system":
                system_prompt = messages[0]["content"]
                messages = messages[1:]
            contents = []
            for message in messages:
                role = "model" if message["role"] == "assistant" else "user"
                contents.append({"role": role, "parts": [{"text": message["content"]}]})
            payload = {
                "contents": contents,
                "generationConfig": {
                    "maxOutputTokens": self.generation.get("max_tokens", 256),
                    "temperature": self.generation.get("temperature", 0.8),
                    "topP": self.generation.get("top_p", 0.9),
                },
            }
            if system_prompt:
                payload["system_instruction"] = {"parts": [{"text": system_prompt}]}
            response = self._post_google(payload)
            return response["candidates"][0]["content"]["parts"][0]["text"].strip()

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.generation.get("max_tokens", 256),
            "temperature": self.generation.get("temperature", 0.8),
            "top_p": self.generation.get("top_p", 0.9),
        }
        response = self._post_openrouter(payload)
        return response["choices"][0]["message"]["content"].strip()

    def generate_response(self, message, conversation_history=None, behavior_profile=None):
        profile_text = behavior_profile or self.profile_manager.load_profile()
        messages = self._prepare_messages(message, conversation_history, profile_text)
        return self._call_provider(messages)

    def analyze_behavior_profile(self, messages):
        if not messages:
            return ""
        prompt = (
            "Сделай краткий профиль поведения автора переписки: стиль, тон, типичные темы, "
            "манера отвечать. Пиши кратко, без списков действий."
        )
        system_message = {"role": "system", "content": prompt}
        return self._call_provider([system_message] + messages)

    def update_behavior_profile(self, messages, total_messages_seen):
        if not self.profile_manager.should_update(total_messages_seen):
            return self.profile_manager.load_profile()
        windowed = messages[-self.profile_manager.messages_window :]
        profile_text = self.analyze_behavior_profile(windowed)
        if profile_text:
            self.profile_manager.save_profile(profile_text)
            self.profile_manager.record_messages_seen(total_messages_seen)
        return profile_text
