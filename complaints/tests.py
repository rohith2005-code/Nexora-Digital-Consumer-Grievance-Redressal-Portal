from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Complaint, ComplaintTimeline
from datetime import date


class ConsumerGrievanceSystemTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Create staff officer
        self.staff_user = User.objects.create_user(
            username='test_officer',
            password='password123',
            is_staff=True,
            email='officer@test.com'
        )

        # Create consumer user
        self.consumer_user = User.objects.create_user(
            username='test_consumer',
            password='password123',
            is_staff=False,
            email='consumer@test.com'
        )

        # Create sample complaint
        self.complaint = Complaint.objects.create(
            user=self.consumer_user,
            product_name='LG Refrigerator 260L',
            category='Home Appliance',
            seller='LG Direct Online',
            purchase_date=date(2026, 8, 10),
            amount_paid=28500.00,
            complaint_type='Defective Product',
            description='Compressor cooling not functioning upon initial delivery.',
            expected_resolution='Replacement',
            priority='High',
            status='Submitted'
        )

    def test_complaint_id_auto_generation(self):
        """Verify that complaint_id is automatically generated in CMP-YYYY-XXXXX format."""
        self.assertTrue(self.complaint.complaint_id.startswith('CMP-2026-'))
        self.assertEqual(str(self.complaint), f"{self.complaint.complaint_id} - LG Refrigerator 260L (Submitted)")

    def test_role_based_redirection(self):
        """Staff users should be redirected to admin portal; consumers to consumer dashboard."""
        # Test consumer login redirection
        self.client.login(username='test_consumer', password='password123')
        response = self.client.get(reverse('login_redirect'), follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('consumer_dashboard'))
        self.client.logout()

        # Test officer login redirection
        self.client.login(username='test_officer', password='password123')
        response = self.client.get(reverse('login_redirect'), follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('admin_dashboard'))

    def test_public_tracking_web(self):
        """Public tracking page should resolve grievance details without requiring authentication."""
        response = self.client.get(reverse('track_complaint') + f'?complaint_id={self.complaint.complaint_id}')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.complaint.complaint_id)
        self.assertContains(response, 'LG Refrigerator 260L')
        self.assertContains(response, 'Submitted')

    def test_public_tracking_api(self):
        """DRF REST API tracking endpoint should return valid JSON."""
        response = self.client.get(reverse('api_complaint_track', kwargs={'complaint_id': self.complaint.complaint_id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['complaint_id'], self.complaint.complaint_id)
        self.assertEqual(response.json()['product_name'], 'LG Refrigerator 260L')

    def test_consumer_can_file_complaint(self):
        """Consumer can register a complaint via form POST."""
        self.client.login(username='test_consumer', password='password123')
        payload = {
            'product_name': 'Sony Bravia TV',
            'category': 'Electronics',
            'seller': 'Croma India',
            'purchase_date': '2026-08-15',
            'amount_paid': '45000.00',
            'complaint_type': 'Damaged Product',
            'priority': 'Medium',
            'expected_resolution': 'Refund',
            'description': 'Display panel cracked upon unboxing by technician.',
        }
        response = self.client.post(reverse('complaint_create'), payload, follow=True)
        self.assertEqual(response.status_code, 200)
        new_complaint = Complaint.objects.filter(product_name='Sony Bravia TV').first()
        self.assertIsNotNone(new_complaint)
        self.assertEqual(new_complaint.user, self.consumer_user)
        self.assertTrue(new_complaint.complaint_id.startswith('CMP-2026-'))

    def test_ai_duplicate_detection(self):
        """Test NLP duplicate and similarity detection engine."""
        from .ai_detector import evaluate_complaint_similarity, find_similar_complaints

        # Create a similar complaint
        duplicate_complaint = Complaint.objects.create(
            user=self.consumer_user,
            product_name='LG Refrigerator 260L Frost Free',
            category='Home Appliance',
            seller='LG Direct Online',
            purchase_date=date(2026, 8, 12),
            amount_paid=28990.00,
            complaint_type='Defective Product',
            description='Refrigerator compressor is not cooling at all since first delivery.',
            expected_resolution='Replacement',
            priority='High',
            status='Submitted'
        )

        # Evaluate similarity
        sim_result = evaluate_complaint_similarity(self.complaint, duplicate_complaint)
        self.assertGreaterEqual(sim_result['score'], 60.0)
        self.assertTrue(sim_result['is_similar'])
        self.assertTrue(any('cooling' in kw or 'compressor' in kw or 'refrigerator' in kw for kw in sim_result['matched_keywords']))

        # Test find_similar_complaints function
        matches = find_similar_complaints(duplicate_complaint, threshold=50.0)
        self.assertTrue(len(matches) >= 1)
        self.assertEqual(matches[0]['complaint'].id, self.complaint.id)

    def test_sla_monitoring_and_automatic_escalation(self):
        """Test automatic SLA deadline calculation and escalation on breach."""
        from django.utils import timezone
        from datetime import timedelta
        from .sla_engine import check_and_escalate_overdue_complaints

        # Ensure complaint has an SLA deadline set
        self.assertIsNotNone(self.complaint.sla_deadline)
        self.assertFalse(self.complaint.is_sla_breached)

        # Simulate SLA breach by setting deadline in past
        self.complaint.sla_deadline = timezone.now() - timedelta(hours=5)
        self.complaint.save()

        self.assertTrue(self.complaint.is_sla_breached)
        self.assertIn("Overdue", self.complaint.sla_time_display)

        # Trigger SLA engine escalation check
        escalated_count = check_and_escalate_overdue_complaints()
        self.complaint.refresh_from_db()

        self.assertGreaterEqual(escalated_count, 1)
        self.assertTrue(self.complaint.is_escalated)
        self.assertEqual(self.complaint.status, 'Escalation Required')

        # Verify automated timeline audit entry
        latest_timeline = self.complaint.timeline.last()
        self.assertIsNotNone(latest_timeline)
        self.assertEqual(latest_timeline.status, 'Escalation Required')
        self.assertIn("SLA BREACH", latest_timeline.remarks)

    def test_ai_assistant_api_faq_and_tracking(self):
        """Test the AI Assistant conversational REST API."""
        # 1. Test FAQ query
        response = self.client.post(
            reverse('api_assistant'),
            data={'message': 'How can I report a damaged product?'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        reply = response.json().get('reply', '')
        self.assertIn("register", reply.lower())

        # 2. Test Live Complaint ID lookup via Assistant
        response = self.client.post(
            reverse('api_assistant'),
            data={'message': f"What is the status of {self.complaint.complaint_id}?"},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        reply = response.json().get('reply', '')
        self.assertIn(self.complaint.complaint_id, reply)
        self.assertIn('LG Refrigerator 260L', reply)

    def test_complaint_duplicates_api(self):
        """Test API endpoint returning similar complaints for a specific case."""
        self.client.login(username='test_officer', password='password123')
        response = self.client.get(
            reverse('api_complaint_duplicates', kwargs={'complaint_id': self.complaint.complaint_id})
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('target_complaint_id', data)
        self.assertIn('similar_complaints', data)

