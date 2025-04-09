from django.contrib import admin
from .models import Conversation, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('created_at',)
    fields = ('role', 'content', 'created_at')


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'agent', 'created_at', 'message_count')
    list_filter = ('created_at', 'agent')
    search_fields = ('title', 'user__username', 'user__email', 'agent__name')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [MessageInline]

    def message_count(self, obj):
        return obj.messages.count()

    message_count.short_description = 'Messages'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('get_conversation_title', 'role', 'short_content', 'created_at')
    list_filter = ('role', 'created_at', 'conversation__agent')
    search_fields = ('content', 'conversation__title')
    readonly_fields = ('created_at',)

    def get_conversation_title(self, obj):
        return obj.conversation.title

    get_conversation_title.short_description = 'Conversation'

    def short_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content

    short_content.short_description = 'Content'