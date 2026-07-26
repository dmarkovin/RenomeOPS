from .start import router as start_router
from .menu import router as menu_router
from .tasks import router as tasks_router
from .employees import router as employees_router
from .services import router as services_router

routers = [
    start_router,
    menu_router,
    tasks_router,
    employees_router,
    services_router,
]
from .reception.deliveries import router as deliveries_router
routers.append(deliveries_router)
