from typing import Callable, Awaitable, Dict, Any
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
import time
from app.metrics import bot_requests_total, bot_update_latency, bot_errors_total, bot_updates_processed

class MetricsMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Определяем команду или callback
        command = "unknown"
        if isinstance(event, Message) and event.text:
            command = event.text[:50]  # первые 50 символов
        elif isinstance(event, CallbackQuery) and event.data:
            command = event.data[:50]
        # Увеличиваем счётчик запросов
        bot_requests_total.labels(command=command).inc()

        start_time = time.time()
        try:
            result = await handler(event, data)
            # Обработка успешна
            bot_update_latency.labels(handler=command).observe(time.time() - start_time)
            bot_updates_processed.inc()
            return result
        except Exception as e:
            # Логируем ошибку в метрики
            bot_errors_total.labels(error_type=type(e).__name__).inc()
            # Перевыбрасываем, чтобы бот обработал её дальше
            raise
