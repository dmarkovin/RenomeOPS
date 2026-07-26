from .start import router as start_router
from .menu import router as menu_router
from .tasks import router as tasks_router
from .employees import router as employees_router
from .object_navigation import router as object_navigation_router
from .services import router as services_router
from .reception.deliveries import router as deliveries_router

routers = [
    start_router,
    menu_router,
    tasks_router,
    employees_router,
    object_navigation_router,
    services_router,
    deliveries_router,
]
from .passes.passes import router as passes_router
routers.append(passes_router)
from .services.admin import router as services_admin_router
from .services.user import router as services_user_router
# уже должно быть, если нет – добавить
