from .admin import router as admin_router
from .create import router as create_router

router = admin_router
router.include_router(create_router)
