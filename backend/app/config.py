from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AI Dev Team Pipeline"
    debug: bool = False
    database_url: str = "sqlite+aiosqlite:///./pipeline.db"
    cors_origins: list[str] = ["http://localhost:5173"]
    ollama_base_url: str = "http://localhost:11434"
    workspace_dir: str = "~/.ai-dev-team/workspaces"
    developer_config_path: str = "developers.json"
    idle_timeout_seconds: int = 60

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
