from .start import router as start_router
from .menu import router as menu_router
from .employees import router as employees_router
from .tasks import router as tasks_router
from .services import router as services_router          # теперь раньше object_navigation
from .object_navigation import router as object_navigation_router
from .reception.deliveries import router as deliveries_router
from .reception.keys import router as keys_router
from .reception.documents import router as documents_router
from .passes.passes import router as passes_router
from .patrol.patrol import router as patrol_router

routers = [
    start_router,
    menu_router,
    employees_router,
    tasks_router,
    services_router,
    object_navigation_router,
    deliveries_router,
    keys_router,
    documents_router,
    passes_router,
    patrol_router,
]
