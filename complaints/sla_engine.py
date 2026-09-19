"""
Automatic Escalation & SLA Monitoring Engine
Monitors statutory response deadlines and automatically escalates overdue complaints.
"""

from django.utils import timezone
from .models import Complaint, ComplaintTimeline


def check_and_escalate_overdue_complaints():
    """
    Scans active complaints and auto-escalates those that have passed their
    statutory SLA deadline without resolution.
    """
    now = timezone.now()
    active_complaints = Complaint.objects.filter(
        status__in=['Submitted', 'Under Review', 'In Progress', 'Additional Information Required'],
        sla_deadline__lt=now
    )

    escalated_count = 0
    for complaint in active_complaints:
        needs_save = False

        if not complaint.is_escalated:
            complaint.is_escalated = True
            needs_save = True

        if complaint.status != 'Escalation Required':
            old_status = complaint.status
            complaint.status = 'Escalation Required'
            needs_save = True

            # Append automated escalation event to audit timeline
            ComplaintTimeline.objects.create(
                complaint=complaint,
                status='Escalation Required',
                remarks=(
                    f"⚠️ AUTOMATIC SLA BREACH: Grievance remained unresolved beyond the statutory "
                    f"response window ({complaint.priority} Priority). Case automatically escalated "
                    f"to Senior Redressal Officer."
                ),
                performed_by=None  # System automated action
            )
            escalated_count += 1

        if needs_save:
            complaint.save()

    return escalated_count
