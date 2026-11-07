"""Database table models.

Import every table model here so ``SQLModel.metadata.create_all`` sees them.
"""

from app.models.application import Application
from app.models.listing import Listing
from app.models.notification import Notification
from app.models.subscription import Subscription
from app.models.user import User

__all__ = [
    "User",
    "Listing",
    "Application",
    "Subscription",
    "Notification",
]
