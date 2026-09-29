from aiogram import Router

from . import common, order


def build_root_router() -> Router:
    """Assemble all routers. Routers are module singletons, so call this once per process."""
    root = Router(name="root")
    root.include_routers(common.router, order.router, common.fallback_router, common.stale_callback_router)
    return root
