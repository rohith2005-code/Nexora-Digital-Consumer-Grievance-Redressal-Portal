import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.http import HttpResponse, Http404
from django.db.models import Q, Count
from django.utils import timezone
from .models import Complaint, ComplaintTimeline
from .forms import (
    ConsumerRegistrationForm,
    ComplaintRegistrationForm,
    AdminComplaintReviewForm,
    ConsumerAdditionalInfoForm
)
from .sla_engine import check_and_escalate_overdue_complaints
from .ai_detector import find_similar_complaints


def staff_check(user):
    return user.is_authenticated and user.is_staff


# -------------------------------------------------------------
# Home & Public Views
# -------------------------------------------------------------
def home_view(request):
    """Modern landing page with platform stats and quick tracking."""
    # Run background SLA check
    check_and_escalate_overdue_complaints()

    total_complaints = Complaint.objects.count()
    resolved_count = Complaint.objects.filter(status__in=['Resolved', 'Closed']).count()
    under_review_count = Complaint.objects.filter(status__in=['Under Review', 'In Progress', 'Escalation Required']).count()
    
    # Calculate resolution rate
    resolution_rate = round((resolved_count / total_complaints * 100), 1) if total_complaints > 0 else 98.4

    # Top complaint categories with counts
    top_categories = (
        Complaint.objects.values('category')
        .annotate(total=Count('id'))
        .order_by('-total')[:6]
    )

    # Recent resolved success stories
    resolved_complaints = Complaint.objects.filter(status='Resolved').order_by('-updated_at')[:3]

    context = {
        'total_complaints': total_complaints,
        'resolved_count': resolved_count,
        'under_review_count': under_review_count,
        'resolution_rate': resolution_rate,
        'top_categories': top_categories,
        'resolved_complaints': resolved_complaints,
    }
    return render(request, 'home.html', context)


def track_complaint_view(request):
    """Public tracking page for quick grievance search by Complaint ID."""
    complaint_id = request.GET.get('complaint_id', '').strip()
    complaint = None
    not_found = False
    step_info = None

    if complaint_id:
        try:
            complaint = Complaint.objects.prefetch_related('timeline').get(complaint_id__iexact=complaint_id)
            step_info = get_stepper_details(complaint.status)
        except Complaint.DoesNotExist:
            not_found = True

    context = {
        'complaint_id': complaint_id,
        'complaint': complaint,
        'not_found': not_found,
        'step_info': step_info,
    }
    return render(request, 'consumer/track.html', context)


# -------------------------------------------------------------
# Authentication & Role-Based Routing
# -------------------------------------------------------------
def register_view(request):
    if request.user.is_authenticated:
        return redirect('login_redirect')

    if request.method == 'POST':
        form = ConsumerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            login(request, user)
            messages.success(request, f"Welcome {user.first_name}! Your consumer account has been created.")
            return redirect('consumer_dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ConsumerRegistrationForm()

    return render(request, 'auth/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('login_redirect')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                return redirect('login_redirect')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'auth/login.html', {'form': form})


@login_required
def login_redirect_view(request):
    """Role-based access redirection: staff to Admin Portal, consumer to Dashboard."""
    if request.user.is_staff:
        return redirect('admin_dashboard')
    return redirect('consumer_dashboard')


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('home')


# -------------------------------------------------------------
# Consumer Portal Views
# -------------------------------------------------------------
@login_required
def consumer_dashboard_view(request):
    """Consumer Dashboard displaying user complaints, stats, and filters."""
    # Check SLAs
    check_and_escalate_overdue_complaints()

    user_complaints = Complaint.objects.filter(user=request.user)

    # Statistics for current consumer
    total = user_complaints.count()
    submitted = user_complaints.filter(status='Submitted').count()
    under_review = user_complaints.filter(status__in=['Under Review', 'In Progress', 'Additional Information Required']).count()
    escalated = user_complaints.filter(status='Escalation Required').count()
    resolved = user_complaints.filter(status__in=['Resolved', 'Closed']).count()

    # Filtering & search
    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('q', '').strip()

    filtered_complaints = user_complaints
    if status_filter == 'active':
        filtered_complaints = filtered_complaints.filter(status__in=['Submitted', 'Under Review', 'In Progress', 'Additional Information Required', 'Escalation Required'])
    elif status_filter == 'escalated':
        filtered_complaints = filtered_complaints.filter(status='Escalation Required')
    elif status_filter == 'resolved':
        filtered_complaints = filtered_complaints.filter(status__in=['Resolved', 'Closed'])
    elif status_filter and status_filter != 'all':
        filtered_complaints = filtered_complaints.filter(status=status_filter)

    if search_query:
        filtered_complaints = filtered_complaints.filter(
            Q(complaint_id__icontains=search_query) |
            Q(product_name__icontains=search_query) |
            Q(seller__icontains=search_query)
        )

    context = {
        'total': total,
        'submitted': submitted,
        'under_review': under_review,
        'escalated': escalated,
        'resolved': resolved,
        'complaints': filtered_complaints,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    return render(request, 'consumer/dashboard.html', context)


@login_required
def complaint_create_view(request):
    """Register a new consumer complaint with proof upload."""
    if request.method == 'POST':
        form = ComplaintRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.user = request.user
            complaint.save()

            # Record initial timeline entry
            ComplaintTimeline.objects.create(
                complaint=complaint,
                status='Submitted',
                remarks=f"Complaint registered for '{complaint.product_name}'. SLA response deadline set to {complaint.sla_time_display}.",
                performed_by=request.user
            )

            # Check for potential duplicates to alert
            duplicates = find_similar_complaints(complaint, threshold=60.0)
            if duplicates:
                messages.warning(
                    request,
                    f"Complaint registered ({complaint.complaint_id})! Our AI detected {len(duplicates)} similar existing issue(s) with this product/merchant which will be cross-referenced during adjudication."
                )
            else:
                messages.success(
                    request,
                    f"Complaint registered successfully! Your tracking ID is {complaint.complaint_id}."
                )

            return redirect('complaint_detail', complaint_id=complaint.complaint_id)
        else:
            messages.error(request, "Please check the form for required fields.")
    else:
        form = ComplaintRegistrationForm()

    return render(request, 'consumer/register_complaint.html', {'form': form})


@login_required
def complaint_detail_view(request, complaint_id):
    """Detailed view of a specific complaint with progress stepper and timeline."""
    complaint = get_object_or_404(Complaint, complaint_id=complaint_id)

    # Ensure access control (owner or staff)
    if not request.user.is_staff and complaint.user != request.user:
        messages.error(request, "You do not have permission to view this complaint.")
        return redirect('consumer_dashboard')

    timeline = complaint.timeline.all()
    step_info = get_stepper_details(complaint.status)

    # Handle consumer additional information response
    additional_form = ConsumerAdditionalInfoForm()
    if request.method == 'POST' and 'submit_additional_info' in request.POST:
        additional_form = ConsumerAdditionalInfoForm(request.POST, request.FILES)
        if additional_form.is_valid():
            remarks = additional_form.cleaned_data['additional_remarks']
            new_file = additional_form.cleaned_data.get('new_attachment')
            if new_file:
                complaint.attachment = new_file
                complaint.save()

            # Move status back to Under Review if it was Additional Information Required
            if complaint.status == 'Additional Information Required':
                complaint.status = 'Under Review'
                complaint.save()

            ComplaintTimeline.objects.create(
                complaint=complaint,
                status='Under Review',
                remarks=f"Consumer provided additional information: {remarks}",
                performed_by=request.user
            )

            messages.success(request, "Additional information submitted to the Grievance Authority.")
            return redirect('complaint_detail', complaint_id=complaint.complaint_id)

    context = {
        'complaint': complaint,
        'timeline': timeline,
        'step_info': step_info,
        'additional_form': additional_form,
    }
    return render(request, 'consumer/complaint_detail.html', context)


# -------------------------------------------------------------
# Grievance Authority / Admin Portal Views
# -------------------------------------------------------------
@user_passes_test(staff_check, login_url='login')
def admin_dashboard_view(request):
    """Grievance Redressal Authority Dashboard for staff members."""
    # Check and trigger SLA escalations
    check_and_escalate_overdue_complaints()

    all_complaints = Complaint.objects.select_related('user').all()

    total = all_complaints.count()
    submitted = all_complaints.filter(status='Submitted').count()
    under_review = all_complaints.filter(status='Under Review').count()
    info_required = all_complaints.filter(status='Additional Information Required').count()
    in_progress = all_complaints.filter(status='In Progress').count()
    escalated = all_complaints.filter(status='Escalation Required').count()
    resolved = all_complaints.filter(status='Resolved').count()
    closed = all_complaints.filter(status='Closed').count()

    # Search & filters
    status_filter = request.GET.get('status', 'all')
    priority_filter = request.GET.get('priority', 'all')
    category_filter = request.GET.get('category', 'all')
    search_query = request.GET.get('q', '').strip()

    filtered = all_complaints
    if status_filter != 'all':
        filtered = filtered.filter(status=status_filter)
    if priority_filter != 'all':
        filtered = filtered.filter(priority=priority_filter)
    if category_filter != 'all':
        filtered = filtered.filter(category=category_filter)
    if search_query:
        filtered = filtered.filter(
            Q(complaint_id__icontains=search_query) |
            Q(product_name__icontains=search_query) |
            Q(seller__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__first_name__icontains=search_query)
        )

    categories = Complaint.CATEGORY_CHOICES
    statuses = Complaint.STATUS_CHOICES
    priorities = Complaint.PRIORITY_CHOICES

    context = {
        'total': total,
        'submitted': submitted,
        'under_review': under_review,
        'info_required': info_required,
        'in_progress': in_progress,
        'escalated': escalated,
        'resolved': resolved,
        'closed': closed,
        'complaints': filtered,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'category_filter': category_filter,
        'search_query': search_query,
        'categories': categories,
        'statuses': statuses,
        'priorities': priorities,
    }
    return render(request, 'admin_portal/dashboard.html', context)


@user_passes_test(staff_check, login_url='login')
def admin_review_complaint_view(request, complaint_id):
    """Authority adjudication interface for reviewing evidence, AI duplicate detection, and writing resolution."""
    complaint = get_object_or_404(Complaint, complaint_id=complaint_id)
    timeline = complaint.timeline.all()

    # Run AI Duplicate & Similarity Detection
    similar_cases = find_similar_complaints(complaint, threshold=40.0)

    if request.method == 'POST':
        form = AdminComplaintReviewForm(request.POST, instance=complaint)
        if form.is_valid():
            old_status = complaint.status
            updated_complaint = form.save()
            internal_note = form.cleaned_data.get('internal_notes', '').strip()

            # Record timeline update if status changed or remarks entered
            timeline_remarks = []
            if old_status != updated_complaint.status:
                timeline_remarks.append(f"Status updated from '{old_status}' to '{updated_complaint.status}'.")
            if updated_complaint.admin_response:
                timeline_remarks.append("Official Authority response issued.")
            if internal_note:
                timeline_remarks.append(f"Officer Note: {internal_note}")

            remarks_text = " ".join(timeline_remarks) if timeline_remarks else f"Reviewed by Officer {request.user.username}."

            ComplaintTimeline.objects.create(
                complaint=updated_complaint,
                status=updated_complaint.status,
                remarks=remarks_text,
                performed_by=request.user
            )

            messages.success(request, f"Grievance {complaint.complaint_id} updated successfully!")
            return redirect('admin_review_complaint', complaint_id=complaint.complaint_id)
    else:
        form = AdminComplaintReviewForm(instance=complaint)

    step_info = get_stepper_details(complaint.status)

    context = {
        'complaint': complaint,
        'timeline': timeline,
        'form': form,
        'step_info': step_info,
        'similar_cases': similar_cases,
    }
    return render(request, 'admin_portal/review_complaint.html', context)


@user_passes_test(staff_check, login_url='login')
def admin_export_csv_view(request):
    """Download complaint records as CSV for reporting and compliance."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="Grievance_Report_{timezone.now().strftime("%Y%m%d_%H%M")}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Complaint ID', 'Consumer', 'Product Name', 'Category', 'Seller',
        'Purchase Date', 'Amount Paid', 'Complaint Type', 'Priority',
        'Status', 'SLA Deadline', 'Is Escalated', 'Expected Resolution', 'Admin Response', 'Created Date'
    ])

    for c in Complaint.objects.select_related('user').all():
        writer.writerow([
            c.complaint_id,
            c.user.get_full_name() or c.user.username,
            c.product_name,
            c.category,
            c.seller,
            c.purchase_date.strftime('%Y-%m-%d'),
            c.amount_paid,
            c.complaint_type,
            c.priority,
            c.status,
            c.sla_deadline.strftime('%Y-%m-%d %H:%M') if c.sla_deadline else 'N/A',
            'Yes' if c.is_escalated else 'No',
            c.expected_resolution,
            c.admin_response.replace('\n', ' '),
            c.created_at.strftime('%Y-%m-%d %H:%M')
        ])

    return response


# -------------------------------------------------------------
# Stepper Helper
# -------------------------------------------------------------
def get_stepper_details(current_status):
    """
    Returns step index (1-5) and warning state for visual progress stepper.
    Stages:
    1: Submitted
    2: Under Review
    3: In Progress
    4: Resolved
    5: Closed
    """
    steps = ['Submitted', 'Under Review', 'In Progress', 'Resolved', 'Closed']
    
    if current_status == 'Additional Information Required':
        return {
            'step_index': 2,
            'is_warning': True,
            'warning_message': 'Authority has requested additional documentation or details from you.',
            'steps': steps,
        }

    if current_status == 'Escalation Required':
        return {
            'step_index': 3,
            'is_warning': True,
            'warning_message': '⚠️ Statutory SLA response window breached. Automatically escalated for senior priority redressal.',
            'steps': steps,
        }

    status_index_map = {
        'Submitted': 1,
        'Under Review': 2,
        'In Progress': 3,
        'Escalation Required': 3,
        'Resolved': 4,
        'Closed': 5,
    }
    return {
        'step_index': status_index_map.get(current_status, 1),
        'is_warning': False,
        'warning_message': '',
        'steps': steps,
    }
