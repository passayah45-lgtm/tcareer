class PrivacyService:
    @staticmethod
    def get_settings(user):
        from apps.users.models import UserPrivacySettings

        settings, _ = UserPrivacySettings.objects.get_or_create(
            user=user,
            defaults={
                "public_profile": getattr(user, "is_public_profile", True),
            },
        )
        return settings

    @staticmethod
    def _existing_settings(user):
        from django.core.exceptions import ObjectDoesNotExist

        try:
            return user.privacy_settings
        except ObjectDoesNotExist:
            return None

    @staticmethod
    def public_profile_enabled(user) -> bool:
        settings = PrivacyService._existing_settings(user)
        return settings.public_profile if settings else getattr(user, "is_public_profile", True)

    @staticmethod
    def recruiter_resume_visible(user) -> bool:
        settings = PrivacyService._existing_settings(user)
        return settings.recruiter_resume_visibility if settings else True

    @staticmethod
    def recruiter_portfolio_visible(user) -> bool:
        settings = PrivacyService._existing_settings(user)
        return settings.recruiter_portfolio_visibility if settings else True

    @staticmethod
    def allow_recruiter_contact(user) -> bool:
        settings = PrivacyService._existing_settings(user)
        return settings.allow_recruiter_contact if settings else True

    @staticmethod
    def open_to_work(user) -> bool:
        settings = PrivacyService._existing_settings(user)
        return settings.open_to_work if settings else False

    @staticmethod
    def allow_analytics(user) -> bool:
        settings = PrivacyService._existing_settings(user)
        return settings.allow_analytics if settings else True

    @staticmethod
    def allow_ai_analysis(user) -> bool:
        settings = PrivacyService._existing_settings(user)
        return settings.allow_ai_analysis if settings else True
