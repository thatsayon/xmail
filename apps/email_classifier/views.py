from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import get_object_or_404
from .models import DraftResponse


class EmailInquiryView(APIView):
    def post(self, request):
        draft_id = request.data.get("draft_id")

        if not draft_id:
            return Response({"error": "Draft ID not provided"}, status=400)
        
        draft_mail = get_object_or_404(DraftResponse, id=draft_id)
        
        if not draft_mail:
            return Response({"error": "Draft not found"}, status=404)
        
        if draft_mail.is_send:
            return Response({"error": "Draft already sent"}, status=400)

        # Send email
        subject = f"[Reply to {draft_mail.email.subject}"
        text_content = draft_mail.draft_body

        try:
            msg = EmailMultiAlternatives(subject, text_content, from_email=None, to=[draft_mail.email.sender])
            msg.attach_alternative(text_content, "text/plain")
            msg.send()
            draft_mail.is_send = True
            draft_mail.sent_at = draft_mail.created_at
            draft_mail.save()
            return Response({"success": "Email sent"}, status=200)
        except Exception as e:
            return Response({"error": "Failed to send email"}, status=500)