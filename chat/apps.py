from django.apps import AppConfig
from django.conf import settings
import logging
import re


logger = logging.getLogger(__name__)
_startup_warning_logged = False


class ChatConfig(AppConfig):
    name = 'chat'

    def ready(self):
        global _startup_warning_logged
        if _startup_warning_logged:
            return

        raw_key = (getattr(settings, 'OPENROUTER_API_KEY', '') or '').strip()
        # OpenRouter keys typically begin with "sk-or-v1-" and should not include spaces.
        looks_valid = bool(re.match(r'^sk-or-v1-[A-Za-z0-9_-]{16,}$', raw_key))

        if not raw_key:
            logger.warning('OPENROUTER_API_KEY is missing. OpenRouter calls will fail with 401.')
            _startup_warning_logged = True
            return

        if raw_key.lower().startswith('bearer '):
            logger.warning("OPENROUTER_API_KEY should not include 'Bearer ' prefix.")
            _startup_warning_logged = True
            return

        if not looks_valid:
            logger.warning('OPENROUTER_API_KEY looks malformed. Verify the key value in .env.')
            _startup_warning_logged = True
            return

        _startup_warning_logged = True
