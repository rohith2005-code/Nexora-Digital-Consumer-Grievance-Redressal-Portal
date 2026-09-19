from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from .models import Complaint, ComplaintTimeline
from .serializers import ComplaintSerializer, ComplaintTrackSerializer
from .assistant import get_ai_assistant_response
from .ai_detector import find_similar_complaints


class ComplaintListCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.is_staff:
            complaints = Complaint.objects.all()
        else:
            complaints = Complaint.objects.filter(user=request.user)
        serializer = ComplaintSerializer(complaints, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        serializer = ComplaintSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            complaint = serializer.save(user=request.user)
            # Create initial timeline entry
            ComplaintTimeline.objects.create(
                complaint=complaint,
                status='Submitted',
                remarks='Complaint submitted by consumer via API.',
                performed_by=request.user
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ComplaintDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk, user):
        if user.is_staff:
            return get_object_or_404(Complaint, pk=pk)
        return get_object_or_404(Complaint, pk=pk, user=user)

    def get(self, request, pk):
        complaint = self.get_object(pk, request.user)
        serializer = ComplaintSerializer(complaint, context={'request': request})
        return Response(serializer.data)


class ComplaintTrackPublicAPIView(APIView):
    """Public tracking endpoint by complaint_id (e.g. /api/track/CMP-2026-00125/)"""
    permission_classes = [permissions.AllowAny]

    def get(self, request, complaint_id):
        complaint = get_object_or_404(Complaint, complaint_id__iexact=complaint_id.strip())
        serializer = ComplaintTrackSerializer(complaint)
        return Response(serializer.data)


class GrievanceStatsAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        total = Complaint.objects.count()
        submitted = Complaint.objects.filter(status='Submitted').count()
        under_review = Complaint.objects.filter(status='Under Review').count()
        info_req = Complaint.objects.filter(status='Additional Information Required').count()
        in_progress = Complaint.objects.filter(status='In Progress').count()
        escalated = Complaint.objects.filter(status='Escalation Required').count()
        resolved = Complaint.objects.filter(status='Resolved').count()
        closed = Complaint.objects.filter(status='Closed').count()

        return Response({
            'total_complaints': total,
            'submitted': submitted,
            'under_review': under_review,
            'additional_info_required': info_req,
            'in_progress': in_progress,
            'escalated': escalated,
            'resolved': resolved,
            'closed': closed,
            'resolution_rate': f"{round((resolved + closed) / total * 100, 1)}%" if total > 0 else "0.0%",
        })


class AIAssistantAPIView(APIView):
    """Conversational endpoint for the interactive AI Consumer Assistant."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        message = request.data.get('message', '').strip()
        if not message:
            return Response({'error': 'Message cannot be empty.'}, status=status.HTTP_400_BAD_REQUEST)

        reply = get_ai_assistant_response(message)
        return Response({'reply': reply})


class ComplaintDuplicatesAPIView(APIView):
    """API endpoint to find and list potential duplicates for a complaint."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, complaint_id):
        complaint = get_object_or_404(Complaint, complaint_id=complaint_id)
        similar_items = find_similar_complaints(complaint)

        results = []
        for item in similar_items:
            results.append({
                'complaint_id': item['complaint'].complaint_id,
                'product_name': item['complaint'].product_name,
                'seller': item['complaint'].seller,
                'status': item['complaint'].status,
                'score': item['score'],
                'is_duplicate': item['is_duplicate'],
                'matched_keywords': item['matched_keywords'],
            })

        return Response({
            'target_complaint_id': complaint.complaint_id,
            'duplicates_found': len(results),
            'similar_complaints': results
        })
