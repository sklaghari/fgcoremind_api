from rest_framework import serializers
from .models import Document, DocumentChunk


class DocumentSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Document
        fields = ['id', 'title', 'file', 'file_type', 'status', 'status_display', 'created_at', 'total_chunks']
        read_only_fields = ['user', 'status', 'total_chunks', 'created_at']

    def create(self, validated_data):
        # Associate the document with the current user
        validated_data['user'] = self.context['request'].user

        # Extract file type from the file extension
        file = validated_data.get('file')
        if file:
            filename = file.name
            file_extension = filename.split('.')[-1].lower()
            validated_data['file_type'] = file_extension

        return super().create(validated_data)


class DocumentChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentChunk
        fields = ['id', 'document', 'content', 'chunk_index', 'metadata']
        read_only_fields = ['embedding']