from django.contrib import admin
from .models import Complaint, ComplaintTimeline


class ComplaintTimelineInline(admin.TabularInline):
    model = ComplaintTimeline
    extra = 0
    readonly_fields = ('created_at',)


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('complaint_id', 'product_name', 'category', 'complaint_type', 'priority', 'status', 'created_at')
    list_filter = ('status', 'priority', 'category', 'complaint_type', 'created_at')
    search_fields = ('complaint_id', 'product_name', 'seller', 'user__username', 'description')
    readonly_fields = ('complaint_id', 'created_at', 'updated_at')
    inlines = [ComplaintTimelineInline]
    ordering = ('-created_at',)


@admin.register(ComplaintTimeline)
class ComplaintTimelineAdmin(admin.ModelAdmin):
    list_display = ('complaint', 'status', 'performed_by', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('complaint__complaint_id', 'remarks')
