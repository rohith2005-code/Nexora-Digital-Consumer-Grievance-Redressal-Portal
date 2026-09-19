from rest_framework import serializers
from .models import Complaint, ComplaintTimeline


class ComplaintTimelineSerializer(serializers.ModelSerializer):
    performed_by_name = serializers.ReadOnlyField(source='performed_by.username')

    class Meta:
        model = ComplaintTimeline
        fields = ['id', 'status', 'remarks', 'performed_by_name', 'created_at']


class ComplaintSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')
    timeline = ComplaintTimelineSerializer(many=True, read_only=True)

    class Meta:
        model = Complaint
        fields = [
            'id',
            'complaint_id',
            'username',
            'product_name',
            'category',
            'seller',
            'purchase_date',
            'amount_paid',
            'complaint_type',
            'description',
            'expected_resolution',
            'priority',
            'status',
            'attachment',
            'admin_response',
            'created_at',
            'updated_at',
            'timeline',
        ]
        read_only_fields = ['complaint_id', 'created_at', 'updated_at', 'admin_response']


class ComplaintTrackSerializer(serializers.ModelSerializer):
    timeline = ComplaintTimelineSerializer(many=True, read_only=True)

    class Meta:
        model = Complaint
        fields = [
            'complaint_id',
            'product_name',
            'category',
            'seller',
            'complaint_type',
            'expected_resolution',
            'status',
            'admin_response',
            'created_at',
            'updated_at',
            'timeline',
        ]
