import logging

logger = logging.getLogger(__name__)


class AuditService:
    @staticmethod
    def record(
        *,
        actor=None,
        action: str,
        target=None,
        target_type: str = "",
        target_id: str = "",
        organization=None,
        request=None,
        metadata: dict | None = None,
    ):
        from apps.audit.models import AuditLog

        if target is not None:
            target_type = target.__class__.__name__
            target_id = str(getattr(target, "id", ""))

        ip_address = ""
        user_agent = ""
        if request is not None:
            ip_address = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip()
            ip_address = ip_address or request.META.get("REMOTE_ADDR", "")
            user_agent = request.META.get("HTTP_USER_AGENT", "")

        try:
            return AuditLog.objects.create(
                actor=actor if getattr(actor, "is_authenticated", False) else None,
                action=action,
                target_type=target_type,
                target_id=target_id,
                organization_id=getattr(organization, "id", None),
                ip_address=ip_address,
                user_agent=user_agent[:500],
                metadata=metadata or {},
            )
        except Exception as exc:
            logger.warning("Audit log write failed: %s", exc)
            return None
