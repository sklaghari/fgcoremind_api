# views.py for handling document upload and processing
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404

from .models import Document, DocumentChunk
from .serializers import DocumentSerializer, DocumentChunkSerializer
from .document_processor import process_document


class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Document.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document = serializer.save()

        # Trigger document processing
        process_document.delay(document.id)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=['post'])
    def reprocess(self, request, pk=None):
        document = self.get_object()

        # Delete existing chunks
        document.chunks.all().delete()

        # Reset status and trigger processing
        document.status = 'pending'
        document.total_chunks = 0
        document.save()

        process_document.delay(document.id)

        return Response({'status': 'processing started'})

    @action(detail=True, methods=['get'])
    def chunks(self, request, pk=None):
        document = self.get_object()
        chunks = document.chunks.all()
        serializer = DocumentChunkSerializer(chunks, many=True)
        return Response(serializer.data)