"""
Seed script for Digital Consumer Complaint Registration & Grievance Redressal System.
Populates realistic demo complaints across multiple categories and creates default test accounts.
"""

import os
import sys
import django
from datetime import date, timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grievance_core.settings')
django.setup()

from django.contrib.auth.models import User
from complaints.models import Complaint, ComplaintTimeline
from django.core.files.base import ContentFile


def run_seed():
    print("Seeding database...")

    # 1. Create Authority Staff / Admin User
    admin_user, created = User.objects.get_or_create(
        username='officer_admin',
        defaults={
            'first_name': 'Adjudication Officer',
            'last_name': 'Sharma',
            'email': 'grievance.officer@consumercare.gov.in',
            'is_staff': True,
            'is_superuser': True,
        }
    )
    admin_user.set_password('adminpass123')
    admin_user.save()
    print(f"Created/Updated Officer Admin: {admin_user.username} (Password: adminpass123)")

    # 2. Create Sample Consumer Users
    consumer_rahul, _ = User.objects.get_or_create(
        username='rahul_consumer',
        defaults={
            'first_name': 'Rahul',
            'last_name': 'Verma',
            'email': 'rahul.verma@example.com',
            'is_staff': False,
        }
    )
    consumer_rahul.set_password('consumerpass123')
    consumer_rahul.save()

    consumer_priya, _ = User.objects.get_or_create(
        username='priya_consumer',
        defaults={
            'first_name': 'Priya',
            'last_name': 'Nair',
            'email': 'priya.nair@example.com',
            'is_staff': False,
        }
    )
    consumer_priya.set_password('consumerpass123')
    consumer_priya.save()
    print("Created Consumers: rahul_consumer, priya_consumer")

    # Clear old seeded complaints for clean restart
    Complaint.objects.all().delete()

    # Sample demo complaints
    sample_data = [
        {
            'user': consumer_rahul,
            'product_name': 'Samsung 7kg Front Load Washing Machine',
            'category': 'Home Appliance',
            'seller': 'XYZ Electronics & Retail Pvt Ltd',
            'purchase_date': date.today() - timedelta(days=25),
            'amount_paid': 35000.00,
            'complaint_type': 'Damaged Product',
            'expected_resolution': 'Replacement',
            'priority': 'High',
            'status': 'Under Review',
            'description': (
                "The washing machine was received with severe physical transit denting on the side drum and "
                "the digital control panel does not turn on. Customer support refused to replace it citing "
                "that package was opened after delivery boy left."
            ),
            'admin_response': (
                "Notice issued to XYZ Electronics under Consumer Protection Rules. The seller has been given 7 days "
                "to arrange replacement inspection."
            ),
            'timeline': [
                ('Submitted', 'Complaint registered with delivery receipt proofs.', consumer_rahul),
                ('Under Review', 'Grievance officer examined transit damage photos. Formal enquiry sent to manufacturer.', admin_user),
            ]
        },
        {
            'user': consumer_rahul,
            'product_name': 'Apple MacBook Air M2 16GB',
            'category': 'Mobile & Computers',
            'seller': 'TechZone MegaStore Online',
            'purchase_date': date.today() - timedelta(days=40),
            'amount_paid': 94900.00,
            'complaint_type': 'Defective Product',
            'expected_resolution': 'Replacement',
            'priority': 'High',
            'status': 'In Progress',
            'description': (
                "Laptop screen exhibits intermittent pink horizontal flickering lines and heating issues within "
                "15 days of purchase. Authorized service centre claiming liquid damage without any corrosion evidence."
            ),
            'admin_response': (
                "Independent technical verification report summoned from Apple Authorized Regional Center. Hearing scheduled."
            ),
            'timeline': [
                ('Submitted', 'Consumer registered complaint with diagnostic screenshots.', consumer_rahul),
                ('Under Review', 'Case verified by Grievance Officer.', admin_user),
                ('In Progress', 'Technical assessment report ordered from regional inspection team.', admin_user),
            ]
        },
        {
            'user': consumer_priya,
            'product_name': 'Sony WH-1000XM5 Wireless Headphones',
            'category': 'Electronics',
            'seller': 'SoundPro Audio Emporium',
            'purchase_date': date.today() - timedelta(days=12),
            'amount_paid': 28990.00,
            'complaint_type': 'Warranty Issue',
            'expected_resolution': 'Repair',
            'priority': 'Medium',
            'status': 'Additional Information Required',
            'description': (
                "The right ear-cup active noise cancellation sensor failed. Service centre demands ₹4,500 claiming "
                "import grey-market unit despite purchase invoice showing GST."
            ),
            'admin_response': (
                "Please upload a clear photograph of the product serial number printed on the inside headband and the GST tax invoice."
            ),
            'timeline': [
                ('Submitted', 'Complaint filed by consumer.', consumer_priya),
                ('Additional Information Required', 'Officer requested clear serial number photo and invoice copy.', admin_user),
            ]
        },
        {
            'user': consumer_priya,
            'product_name': 'ExpressDelivery Courier Consignment',
            'category': 'Delivery & Logistics',
            'seller': 'FastTrack Logistics Pvt Ltd',
            'purchase_date': date.today() - timedelta(days=18),
            'amount_paid': 3850.00,
            'complaint_type': 'Product Not Delivered',
            'expected_resolution': 'Refund',
            'priority': 'Medium',
            'status': 'Resolved',
            'description': (
                "Consignment tracking showed 'Delivered to recipient' at 11:30 PM, but security gate records confirm "
                "no delivery person arrived. Package contained festival gifts worth ₹3,850."
            ),
            'admin_response': (
                "Logistics provider admitted false delivery scanning by subcontractor. Full refund of ₹3,850 approved and credited to consumer bank account."
            ),
            'timeline': [
                ('Submitted', 'Grievance submitted by consumer.', consumer_priya),
                ('Under Review', 'Notice served to logistics regional manager.', admin_user),
                ('In Progress', 'Internal delivery GPS logs examined.', admin_user),
                ('Resolved', 'Full refund settlement confirmed by merchant gateway.', admin_user),
            ]
        },
        {
            'user': consumer_rahul,
            'product_name': 'Airtel Xstream Fiber 300 Mbps',
            'category': 'Internet & Telecom',
            'seller': 'Bharti Airtel Broadband Service',
            'purchase_date': date.today() - timedelta(days=60),
            'amount_paid': 1499.00,
            'complaint_type': 'Service Issue',
            'expected_resolution': 'Compensation',
            'priority': 'Low',
            'status': 'Closed',
            'description': (
                "Continuous fiber cable breakdown for 14 straight days without any billing rebate or technician visit."
            ),
            'admin_response': (
                "ISP has credited ₹700 pro-rata downtime rebate on consumer account and restored fiber link."
            ),
            'timeline': [
                ('Submitted', 'Consumer filed service disruption grievance.', consumer_rahul),
                ('Under Review', 'Telecommunications grievance unit notified.', admin_user),
                ('Resolved', 'Rebate credit applied to consumer bill.', admin_user),
                ('Closed', 'Matter closed with mutual satisfaction.', admin_user),
            ]
        },
        {
            'user': consumer_priya,
            'product_name': 'Urban Living 3-Seater Solid Sheesham Sofa',
            'category': 'Furniture',
            'seller': 'Urban Teakwood Crafts',
            'purchase_date': date.today() - timedelta(days=8),
            'amount_paid': 26400.00,
            'complaint_type': 'Poor Quality',
            'expected_resolution': 'Repair',
            'priority': 'Medium',
            'status': 'Submitted',
            'description': (
                "The sofa arrived with cracked leg joinery and uneven cushion stitching. Seller is unresponsive on phone."
            ),
            'admin_response': '',
            'timeline': [
                ('Submitted', 'Complaint filed by consumer. Awaiting initial scrutiny.', consumer_priya),
            ]
        },
        # 🔎 AI DUPLICATE DETECTION DEMO CASE (matches the Samsung washing machine complaint above)
        {
            'user': consumer_priya,
            'product_name': 'Samsung 7kg Front Load Washing Machine',
            'category': 'Home Appliance',
            'seller': 'XYZ Electronics & Retail Pvt Ltd',
            'purchase_date': date.today() - timedelta(days=20),
            'amount_paid': 34999.00,
            'complaint_type': 'Damaged Product',
            'expected_resolution': 'Replacement',
            'priority': 'High',
            'status': 'Submitted',
            'description': (
                "Received damaged washing machine upon delivery. The side drum has physical transit dents and "
                "the electronic control panel does not turn on. Seller refuses replacement."
            ),
            'admin_response': '',
            'timeline': [
                ('Submitted', 'Complaint submitted with photo proofs. AI Duplicate Detection flagged similar existing claim.', consumer_priya),
            ]
        },
        # ⏰ SLA BREACH & AUTOMATIC ESCALATION DEMO CASE
        {
            'user': consumer_rahul,
            'product_name': 'PureWater Ro+UV Water Purifier',
            'category': 'Home Appliance',
            'seller': 'AquaTech Solutions Ltd',
            'purchase_date': date.today() - timedelta(days=15),
            'amount_paid': 16500.00,
            'complaint_type': 'Service Issue',
            'expected_resolution': 'Refund',
            'priority': 'High',
            'status': 'Escalation Required',
            'is_escalated': True,
            'sla_deadline': timezone.now() - timedelta(hours=36),
            'description': (
                "Water purifier installation delayed over 3 weeks. Technician failed to attend 4 scheduled "
                "appointments. Customer helpline disconnected calls."
            ),
            'admin_response': (
                "SLA BREACH ESCALATION: Case escalated to Executive Adjudication Officer due to seller non-response."
            ),
            'timeline': [
                ('Submitted', 'Complaint filed by consumer with appointment confirmation logs.', consumer_rahul),
                ('Escalation Required', '⚠️ AUTOMATIC SLA BREACH: Grievance remained unresolved beyond the statutory 24h response window. Case automatically escalated to Senior Redressal Officer.', None),
            ]
        }
    ]

    for item in sample_data:
        timeline_events = item.pop('timeline')
        complaint = Complaint.objects.create(**item)

        # Create sample placeholder invoice
        sample_invoice_content = f"Official Invoice & Bill Proof\nProduct: {complaint.product_name}\nAmount: INR {complaint.amount_paid}\nSeller: {complaint.seller}\nDate: {complaint.purchase_date}"
        complaint.attachment.save(f"invoice_{complaint.complaint_id}.txt", ContentFile(sample_invoice_content.encode('utf-8')), save=True)

        for status_val, remarks_val, user_val in timeline_events:
            ComplaintTimeline.objects.create(
                complaint=complaint,
                status=status_val,
                remarks=remarks_val,
                performed_by=user_val
            )

        print(f"Created Complaint: {complaint.complaint_id} ({complaint.product_name}) -> Status: {complaint.status}")

    print("\nSeed data population completed successfully!")


if __name__ == '__main__':
    run_seed()
