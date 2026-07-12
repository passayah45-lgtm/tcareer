from rest_framework import serializers
from .models import (
    IdentityVerificationDocument,
    VerificationRequest,
    VerificationAction,
    DocumentType,
    SubjectType,
)


class DocumentUploadSerializer(serializers.Serializer):
    document_type = serializers.ChoiceField(choices=DocumentType.choices)
    owner_type = serializers.ChoiceField(choices=SubjectType.choices)
    owner_id = serializers.UUIDField()
    expires_at = serializers.DateField(required=False, allow_null=True)


class IdentityVerificationDocumentSerializer(serializers.ModelSerializer):
    # Safe serializer: never includes s3_bucket or s3_key.

    class Meta:
        model = IdentityVerificationDocument
        fields = [
            "id",
            "owner_type",
            "owner_id",
            "document_type",
            "file_name",
            "file_size",
            "mime_type",
            "is_encrypted",
            "created_at",
            "expires_at",
            "verified_until",
            "is_active",
            "staff_notes",
        ]
        read_only_fields = fields


class VerificationRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerificationRequest
        fields = [
            "id",
            "subject_type",
            "subject_id",
            "status",
            "priority",
            "priority_reason",
            "assigned_to",
            "applicant_notes",
            "reviewer_notes",
            "submitted_at",
            "reviewed_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "priority",
            "priority_reason",
            "assigned_to",
            "reviewer_notes",
            "submitted_at",
            "reviewed_at",
        ]


class VerificationRequestDetailSerializer(serializers.ModelSerializer):
    documents = serializers.SerializerMethodField()

    class Meta:
        model = VerificationRequest
        fields = [
            "id",
            "subject_type",
            "subject_id",
            "status",
            "priority",
            "priority_reason",
            "assigned_to",
            "applicant_notes",
            "reviewer_notes",
            "internal_notes",
            "submitted_at",
            "reviewed_at",
            "documents",
        ]
        read_only_fields = fields

    def get_documents(self, obj):
        docs = IdentityVerificationDocument.objects.filter(
            owner_type=obj.subject_type,
            owner_id=obj.subject_id,
            is_active=True,
        )
        return IdentityVerificationDocumentSerializer(docs, many=True).data


class StaffApproveSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, default="")
    reviewer_notes = serializers.CharField(required=False, allow_blank=True, default="")
    internal_notes = serializers.CharField(required=False, allow_blank=True, default="")


class StaffRejectSerializer(serializers.Serializer):
    reason = serializers.CharField(min_length=10)
    reviewer_notes = serializers.CharField(required=False, allow_blank=True, default="")
    internal_notes = serializers.CharField(required=False, allow_blank=True, default="")


class StaffMoreInfoSerializer(serializers.Serializer):
    reviewer_notes = serializers.CharField(min_length=10)
    internal_notes = serializers.CharField(required=False, allow_blank=True, default="")


class StaffSuspendSerializer(serializers.Serializer):
    reason = serializers.CharField(min_length=10)
    internal_notes = serializers.CharField(required=False, allow_blank=True, default="")


class StaffReinstateSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, default="")
    internal_notes = serializers.CharField(required=False, allow_blank=True, default="")


class SubmitVerificationSerializer(serializers.Serializer):
    subject_type = serializers.ChoiceField(choices=SubjectType.choices)
    subject_id = serializers.UUIDField()
    applicant_notes = serializers.CharField(required=False, allow_blank=True, default="")


class VerificationActionSerializer(serializers.ModelSerializer):
    actor_email = serializers.SerializerMethodField()

    class Meta:
        model = VerificationAction
        fields = [
            "id",
            "actor",
            "actor_email",
            "target_type",
            "target_id",
            "action",
            "previous_status",
            "new_status",
            "reason",
            "notes",
            "ip_address",
            "device",
            "browser",
            "country",
            "city",
            "performed_at",
        ]
        read_only_fields = fields

    def get_actor_email(self, obj):
        if obj.actor:
            return obj.actor.email
        return None