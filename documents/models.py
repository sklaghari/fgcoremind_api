from django.db import models
from accounts.models import User
import os
import uuid


def document_upload_path(instance, filename):
    # Generate a unique filename to avoid collisions
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('documents', str(instance.user.id), filename)


class Document(models.Model):
    PROCESSING_STATUS = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )

    title = models.CharField(max_length=255)
    file = models.FileField(upload_to=document_upload_path)
    file_type = models.CharField(max_length=50)  # pdf, txt, docx, etc.
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    status = models.CharField(max_length=20, choices=PROCESSING_STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Metadata
    total_chunks = models.IntegerField(default=0)

    def __str__(self):
        return self.title


class DocumentChunk(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    content = models.TextField()
    chunk_index = models.IntegerField()
    embedding = models.JSONField(null=True, blank=True)  # Store embedding as JSON
    metadata = models.JSONField(default=dict, blank=True)  # For storing page numbers, sections, etc.

    class Meta:
        ordering = ['chunk_index']
        unique_together = ['document', 'chunk_index']

    def __str__(self):
        return f"{self.document.title} - Chunk {self.chunk_index}"