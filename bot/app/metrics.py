from prometheus_client import Counter, Histogram, Gauge, start_http_server, REGISTRY
import time

# Счётчики ошибок
bot_errors_total = Counter('bot_errors_total', 'Total errors by type', ['error_type'])

# Счётчики запросов
bot_requests_total = Counter('bot_requests_total', 'Total requests by command', ['command'])

# Гистограмма времени обработки
bot_update_latency = Histogram('bot_update_latency_seconds', 'Update processing latency', ['handler'])

# Количество обработанных обновлений
bot_updates_processed = Counter('bot_updates_processed', 'Total processed updates')

# uptime бота (стартуем с 0, обновляем раз в секунду)
bot_uptime = Gauge('bot_uptime_seconds', 'Bot uptime in seconds')
bot_start_time = time.time()

def update_uptime():
    bot_uptime.set(time.time() - bot_start_time)

# Метрики бизнес-логики – будут обновляться из сервисов
tasks_created_total = Counter('tasks_created_total', 'Total tasks created')
tasks_closed_total = Counter('tasks_closed_total', 'Total tasks closed')
tasks_by_status = Gauge('tasks_by_status', 'Tasks by status', ['status'])
passes_active_total = Gauge('passes_active_total', 'Active passes')
deliveries_pending_total = Gauge('deliveries_pending_total', 'Pending deliveries')
users_active_total = Gauge('users_active_total', 'Active users')

# Вспомогательная функция для обновления бизнес-метрик (будет вызываться по расписанию)
async def update_business_metrics():
    from app.services.tasks.service import count_tasks_by_status, get_tasks_by_status
    from app.services.passes.service import count_passes_by_status
    from app.services.reception.delivery_service import get_all_deliveries
    from app.services.employees.service import count_employees

    # Заявки по статусам
    for status in ['created', 'accepted', 'in_progress', 'checking', 'closed', 'waiting', 'paused']:
        count = await count_tasks_by_status(status)
        tasks_by_status.labels(status=status).set(count)

    # Активные пропуска
    active_passes = await count_passes_by_status('active')
    passes_active_total.set(active_passes)

    # Посылки в ожидании
    deliveries = await get_all_deliveries(limit=10000)
    pending = len([d for d in deliveries if d.status == 'pending'])
    deliveries_pending_total.set(pending)

    # Активные пользователи
    active_users = await count_employees(active=True)
    users_active_total.set(active_users)
