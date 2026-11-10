"""配置。

所有「因环境而异」的东西都从这里取，不要散落在代码里。
变量名和 .env.example 里的一一对应。
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="EVAL_")

    api_base_url: str = "https://example.invalid/api"
    api_key: str = ""
    concurrency: int = 8
    log_level: str = "INFO"

    def require_api_key(self) -> str:
        """需要真调 API 时才检查。

        为什么不把 api_key 设成必填？因为用 `--models fake` 跑离线模式时
        根本不需要密钥 —— 那时要求填，只会让第一次试用的人卡在启动报错上。

        「早失败」的原则没变，只是把失败点挪到了**真正需要它的那一刻**。
        """
        if not self.api_key:
            raise ValueError(
                "没有配置 EVAL_API_KEY，无法调用真实模型。\n"
                "  - 想跑离线演示：加 --models fake\n"
                "  - 想调真模型：复制 .env.example 为 .env 并填上密钥"
            )
        return self.api_key


@lru_cache
def get_settings() -> Settings:
    """读配置。

    只读一次，之后拿缓存 —— 环境变量不会在运行中途变，重复解析纯属浪费。
    顺带一提，`get_settings.cache_clear()` 在测试里很好用：
    调一下就能让它重新读一遍环境变量。
    """
    return Settings()
