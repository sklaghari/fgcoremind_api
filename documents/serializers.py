# documents/serializers.py
from rest_framework import serializers
from .models import Document

class DocumentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'title', 'file_type', 'status', 'created_at']