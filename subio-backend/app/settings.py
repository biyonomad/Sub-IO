from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Subio"
    APP_VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    MAX_UPLOAD_SIZE_MB: int = 51200
    MAX_VIDEO_DURATION_MINUTES: int = 120
    MAX_AUDIO_DURATION_MINUTES: int = 120

    TRANSCRIPTION_PROVIDER: str = "local_whisper"
    WHISPER_MODEL: str = "turbo"
    WHISPER_DEVICE: str = "auto"

    ENABLE_TRANSLATION: bool = False
    TRANSLATION_PROVIDER: str = "openai"
    OPENAI_API_KEY: str = ""
    OPENAI_TRANSLATION_MODEL: str = "gpt-4.1-mini"

    STORAGE_DIR: str = "storage"
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def max_upload_size_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def max_video_duration_seconds(self) -> int:
        return self.MAX_VIDEO_DURATION_MINUTES * 60

    @property
    def max_audio_duration_seconds(self) -> int:
        return self.MAX_AUDIO_DURATION_MINUTES * 60

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
