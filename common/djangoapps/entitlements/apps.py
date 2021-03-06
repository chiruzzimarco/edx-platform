"""
Entitlements Application Configuration

Signal handlers are connected here.
"""

from __future__ import absolute_import

from django.apps import AppConfig


class EntitlementsConfig(AppConfig):
    """
    Application Configuration for Entitlements.
    """
    name = u'entitlements'

    def ready(self):
        """
        Connect handlers to signals.
        """
        from . import signals  # pylint: disable=unused-variable
        from .tasks import expire_old_entitlements
