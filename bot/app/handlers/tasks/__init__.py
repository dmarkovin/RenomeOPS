from .create import router as create_router
from .list import router as list_router
from .card import router as card_router
from .assign import router as assign_router

router = create_router
router.include_router(list_router)
router.include_router(card_router)
router.include_router(assign_router)
