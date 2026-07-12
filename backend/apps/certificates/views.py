from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import serializers

from .models import Certificate
from .services import CertificateService


class CertificateSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source="course.title", read_only=True)
    student_name = serializers.CharField(source="user.full_name", read_only=True)
    verify_url = serializers.ReadOnlyField()

    class Meta:
        model = Certificate
        fields = [
            "id", "cert_number", "course_title", "student_name",
            "pdf_url", "verify_url", "is_valid", "is_revoked", "issued_at",
        ]


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_certificates(request):
    """
    GET /api/v1/certificates/

    Returns all certificates earned by the authenticated student.
    """
    certificates = Certificate.objects.filter(
        user=request.user, is_revoked=False
    ).select_related("course").order_by("-issued_at")
    serializer = CertificateSerializer(certificates, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def verify_certificate(request, cert_number):
    """
    GET /api/v1/certificates/verify/{cert_number}/

    Public endpoint. No authentication required.
    Used by employers scanning a QR code to verify a certificate.
    Returns structured JSON that any system can parse.
    """
    result = CertificateService.verify(cert_number)
    status_code = 200 if result["valid"] else 404
    return Response(result, status=status_code)
