from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
from .models import Certificate
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_certificates(request):
    certs = Certificate.objects.filter(user=request.user).order_by('-issued_at')
    data = [
        {
            'id': c.id,
            'language': c.programming_language,
            'score': c.score,
            'certificate_id': c.certificate_id,
            'pdf_url': f"{settings.MEDIA_URL}{c.pdf_path}",
            'issued_at': c.issued_at.strftime('%d %b %Y'),
            'email_sent': c.email_sent,
        }
        for c in certs
    ]
    return Response({'certificates': data})

