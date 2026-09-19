from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random


class Complaint(models.Model):
    # Category Choices
    CATEGORY_CHOICES = [
        ('Electronics', 'Electronics'),
        ('Home Appliance', 'Home Appliance'),
        ('Mobile & Computers', 'Mobile & Computers'),
        ('Fashion & Clothing', 'Fashion & Clothing'),
        ('Food & Beverages', 'Food & Beverages'),
        ('Furniture', 'Furniture'),
        ('Internet & Telecom', 'Internet & Telecom'),
        ('Delivery & Logistics', 'Delivery & Logistics'),
        ('Repair & Maintenance', 'Repair & Maintenance'),
        ('Travel & Transport', 'Travel & Transport'),
        ('Financial & Billing', 'Financial & Billing'),
        ('Other', 'Other Services'),
    ]

    # Complaint Type Choices
    COMPLAINT_TYPES = [
        ('Defective Product', 'Defective Product'),
        ('Damaged Product', 'Damaged Product'),
        ('Wrong Product', 'Wrong Product'),
        ('Product Not Delivered', 'Product Not Delivered'),
        ('Late Delivery', 'Late Delivery'),
        ('Poor Quality', 'Poor Quality'),
        ('Overcharging', 'Overcharging'),
        ('Refund Issue', 'Refund Issue'),
        ('Warranty Issue', 'Warranty Issue'),
        ('Misleading Information', 'Misleading Information'),
        ('Service Issue', 'Service Issue'),
        ('Other', 'Other'),
    ]

    # Expected Resolution Choices
    RESOLUTION_CHOICES = [
        ('Refund', 'Full / Partial Refund'),
        ('Replacement', 'Product Replacement'),
        ('Repair', 'Free Repair Service'),
        ('Delivery', 'Immediate Delivery / Dispatch'),
        ('Warranty Service', 'Warranty Service / Honor Warranty'),
        ('Compensation', 'Financial Compensation for Damages'),
        ('Other', 'Other Remedy'),
    ]

    # Priority Choices
    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
    ]

    # Status Choices (Includes Escalation Required for SLA Monitoring)
    STATUS_CHOICES = [
        ('Submitted', 'Submitted'),
        ('Under Review', 'Under Review'),
        ('Additional Information Required', 'Additional Information Required'),
        ('In Progress', 'In Progress'),
        ('Escalation Required', 'Escalation Required (SLA Breached)'),
        ('Resolved', 'Resolved'),
        ('Closed', 'Closed'),
    ]

    complaint_id = models.CharField(max_length=30, unique=True, editable=False, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaints')
    product_name = models.CharField(max_length=200, help_text='Name of the product or service')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Electronics')
    seller = models.CharField(max_length=200, help_text='Seller, Manufacturer, or Service Provider')
    purchase_date = models.DateField(help_text='Date of purchase or service agreement')
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, help_text='Total amount paid (in ₹)')
    complaint_type = models.CharField(max_length=50, choices=COMPLAINT_TYPES)
    description = models.TextField(help_text='Detailed description of the grievance')
    expected_resolution = models.CharField(max_length=50, choices=RESOLUTION_CHOICES, default='Refund')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Medium')
    status = models.CharField(max_length=40, choices=STATUS_CHOICES, default='Submitted')
    attachment = models.FileField(
        upload_to='complaint_evidence/',
        blank=True,
        null=True,
        help_text='Upload purchase bill, invoice, warranty, product photos or screenshots'
    )
    admin_response = models.TextField(blank=True, default='', help_text='Official response from Grievance Authority')
    
    # SLA Monitoring & Automatic Escalation Fields
    sla_deadline = models.DateTimeField(null=True, blank=True, help_text='Statutory SLA response deadline')
    is_escalated = models.BooleanField(default=False, help_text='Flagged if complaint breached response SLA')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Consumer Complaint'
        verbose_name_plural = 'Consumer Complaints'

    def save(self, *args, **kwargs):
        # Auto-generate unique Complaint ID: CMP-YYYY-XXXXX
        if not self.complaint_id:
            year = timezone.now().year
            total_count = Complaint.objects.count() + 1
            random_salt = random.randint(10, 99)
            self.complaint_id = f"CMP-{year}-{total_count:04d}{random_salt}"
            while Complaint.objects.filter(complaint_id=self.complaint_id).exists():
                random_salt = random.randint(100, 999)
                self.complaint_id = f"CMP-{year}-{total_count:03d}{random_salt}"

        # Calculate SLA deadline based on priority: High=24h, Medium=48h, Low=72h
        if not self.sla_deadline:
            now = timezone.now()
            hours_map = {'High': 24, 'Medium': 48, 'Low': 72}
            sla_hours = hours_map.get(self.priority, 48)
            self.sla_deadline = now + timedelta(hours=sla_hours)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.complaint_id} - {self.product_name} ({self.status})"

    @property
    def is_resolved(self):
        return self.status in ['Resolved', 'Closed']

    @property
    def is_sla_breached(self):
        """Returns True if deadline has passed without final resolution."""
        if self.is_resolved:
            return False
        if not self.sla_deadline:
            return False
        return timezone.now() > self.sla_deadline

    @property
    def sla_time_display(self):
        """Human-readable SLA countdown or breach duration."""
        if self.is_resolved:
            return "Resolved within SLA"
        if not self.sla_deadline:
            return "SLA not set"

        now = timezone.now()
        if now > self.sla_deadline:
            delta = now - self.sla_deadline
            hours = int(delta.total_seconds() // 3600)
            if hours < 24:
                return f"⚠️ Overdue by {hours}h"
            days = delta.days
            return f"⚠️ Overdue by {days}d"
        else:
            delta = self.sla_deadline - now
            hours = int(delta.total_seconds() // 3600)
            if hours < 24:
                return f"{hours}h remaining"
            days = delta.days
            return f"{days}d {hours % 24}h remaining"

    @property
    def sla_badge_class(self):
        if self.is_resolved:
            return "sla-resolved"
        if self.is_sla_breached:
            return "sla-breached"
        now = timezone.now()
        hours_left = (self.sla_deadline - now).total_seconds() / 3600
        if hours_left <= 6:
            return "sla-urgent"
        return "sla-normal"

    @property
    def badge_class(self):
        """Returns CSS badge class for status styling."""
        mapping = {
            'Submitted': 'badge-submitted',
            'Under Review': 'badge-review',
            'Additional Information Required': 'badge-warning',
            'In Progress': 'badge-progress',
            'Escalation Required': 'badge-escalated',
            'Resolved': 'badge-resolved',
            'Closed': 'badge-closed',
        }
        return mapping.get(self.status, 'badge-default')


class ComplaintTimeline(models.Model):
    """Tracks chronological events & status changes for each grievance."""
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='timeline')
    status = models.CharField(max_length=40)
    remarks = models.TextField()
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.complaint.complaint_id} -> {self.status} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"
