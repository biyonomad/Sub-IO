SUPPORTED_LANGUAGES = [
    {"code": "auto", "name": "Auto-detect"},
    {"code": "tr", "name": "Türkçe"},
    {"code": "en", "name": "English"},
    {"code": "de", "name": "Deutsch"},
    {"code": "uk", "name": "Українська"},
]

SUPPORTED_LANGUAGE_CODES = {lang["code"] for lang in SUPPORTED_LANGUAGES}

SUPPORTED_TARGET_LANGUAGES = [
    {"code": "en", "label": "English"},
    {"code": "de", "label": "German"},
    {"code": "tr", "label": "Turkish"},
    {"code": "uk", "label": "Ukrainian"},
]

SUPPORTED_TARGET_LANGUAGE_CODES = {lang["code"] for lang in SUPPORTED_TARGET_LANGUAGES}
