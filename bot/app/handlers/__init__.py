from .start import router as start_router
from .menu import router as menu_router
from .tasks import router as tasks_router
from .employees import router as employees_router

routers = [
    start_router,
    menu_router,
    tasks_router,
    employees_router,
]
