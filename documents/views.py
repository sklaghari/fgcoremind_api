# documents/views.py
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from .models import Document
from .serializers import DocumentListSerializer


class DocumentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DocumentListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Return only documents owned by the requesting user
        return Document.objects.filter(user=self.request.user)