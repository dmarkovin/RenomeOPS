from aiogram.types import ReplyKeyboardRemove
from .admin import router as admin_router
from .user import router as user_router

router = admin_router
router.include_router(user_router)
