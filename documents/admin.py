# admin.py (with improved error tracking)
from django.contrib import admin
from django.utils.html import format_html
from django import forms
from django.contrib import messages
import traceback
import logging
from .models import Document, DocumentChunk
from .document_processor import process_document
import threading

logger = logging.getLogger(__name__)


class DocumentAdminForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'file', 'user','agent']


class DocumentChunkInline(admin.TabularInline):
    model = DocumentChunk
    readonly_fields = ['chunk_index', 'content', 'metadata']
    extra = 0
    can_delete = False
    max_num = 0

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'file_type', 'user', 'agent', 'status_badge', 'total_chunks', 'created_at']
    list_filter = ['status', 'file_type', 'created_at', 'user','agent']
    search_fields = ['title', 'user__email','agent__name']
    readonly_fields = ['file_type', 'status', 'total_chunks', 'created_at', 'updated_at']
    form = DocumentAdminForm
    inlines = [DocumentChunkInline]
    actions = ['process_documents_now', 'process_documents_debug']

    def status_badge(self, obj):
        """Display status as a colored badge"""
        colors = {
            'pending': '#FFA500',  # Orange
            'processing': '#1E90FF',  # Blue
            'completed': '#32CD32',  # Green
            'failed': '#FF0000'  # Red
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 5px;">{}</span>',
            colors.get(obj.status, '#777777'),
            obj.get_status_display()
        )

    status_badge.short_description = 'Status'

    def save_model(self, request, obj, form, change):
        """Extract file type on save"""
        if not change:  # Only for new documents
            # Extract file type from the file extension
            file = obj.file
            if file:
                filename = file.name
                file_extension = filename.split('.')[-1].lower()
                obj.file_type = file_extension

        super().save_model(request, obj, form, change)
        self.message_user(
            request,
            f"Document '{obj.title}' saved. Use the 'Process documents now' action to start processing.",
            level=messages.INFO
        )

    def process_documents_now(self, request, queryset):
        """Process selected documents synchronously with detailed error handling"""
        for document in queryset:
            try:
                self.message_user(request, f"Starting processing for document: {document.title}")

                # Update status to processing manually to confirm status changes work
                document.status = 'processing'
                document.save(update_fields=['status'])

                # Process the document
                result = process_document(document.id)

                # Get the updated document to check status
                updated_doc = Document.objects.get(id=document.id)
                self.message_user(
                    request,
                    f"Document '{document.title}' processing complete. Status: {updated_doc.status}. Result: {result}",
                    level=messages.SUCCESS if updated_doc.status == 'completed' else messages.ERROR
                )
            except Exception as e:
                error_msg = traceback.format_exc()
                logger.error(f"Error processing document {document.id}: {error_msg}")
                self.message_user(
                    request,
                    f"Error processing document '{document.title}': {str(e)}. Check server logs for details.",
                    level=messages.ERROR
                )
                # Ensure status is updated to failed
                document.status = 'failed'
                document.save(update_fields=['status'])

    process_documents_now.short_description = "Process documents now (with detailed feedback)"

    def process_documents_debug(self, request, queryset):
        """Debug version that only updates status to verify status changes work"""
        for document in queryset:
            try:
                # Just update status to verify status changes work
                document.status = 'processing'
                document.save(update_fields=['status'])

                self.message_user(
                    request,
                    f"Document '{document.title}' status updated to 'processing' successfully. No actual processing done.",
                    level=messages.SUCCESS
                )

                # Set it back to completed to show another status change
                document.status = 'completed'
                document.save(update_fields=['status'])

                self.message_user(
                    request,
                    f"Document '{document.title}' status updated to 'completed' successfully. No actual processing done.",
                    level=messages.SUCCESS
                )
            except Exception as e:
                error_msg = traceback.format_exc()
                logger.error(f"Error updating document {document.id} status: {error_msg}")
                self.message_user(
                    request,
                    f"Error updating document '{document.title}' status: {str(e)}",
                    level=messages.ERROR
                )

    process_documents_debug.short_description = "DEBUG: Just update status (no processing)"


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ['id', 'document', 'chunk_index', 'has_embedding']
    list_filter = ['document']
    search_fields = ['document__title', 'content']
    readonly_fields = ['document', 'chunk_index', 'content', 'metadata', 'embedding']

    def has_embedding(self, obj):
        return obj.embedding is not None

    has_embedding.boolean = True
    has_embedding.short_description = 'Has Embedding'

    def has_add_permission(self, request):
        return False
