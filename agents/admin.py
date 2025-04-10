# from django.contrib import admin
# from .models import Agent, AgentPermission
#
# @admin.register(Agent)
# class AgentAdmin(admin.ModelAdmin):
#     list_display = ('name', 'owner', 'model', 'is_public', 'created_at', 'updated_at')
#     list_filter = ('model', 'is_public', 'created_at')
#     search_fields = ('name', 'description', 'owner__username', 'owner__email')
#     readonly_fields = ('created_at', 'updated_at')
#
#     fieldsets = (
#         (None, {
#             'fields': ('name', 'description', 'owner', 'model', 'is_public')
#         }),
#         ('Timestamps', {
#             'fields': ('created_at', 'updated_at'),
#             'classes': ('collapse',)
#         }),
#         ('Configuration', {
#             'fields': ('instructions',),
#             'classes': ('wide',)
#         }),
#     )
#
# @admin.register(AgentPermission)
# class AgentPermissionAdmin(admin.ModelAdmin):
#     list_display = ('agent', 'user')
#     list_filter = ('agent', 'user')
#     search_fields = ('agent__name', 'user__username', 'user__email')
