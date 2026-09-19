"""
AI Consumer Assistant
Provides real-time conversational redressal guidance, automated status lookups by ID,
procedural FAQ explanations, and smart category recommendations.
"""

import re
from .models import Complaint


FAQ_KNOWLEDGE_BASE = {
    'report_damaged': {
        'triggers': ['damaged product', 'report damaged', 'broken item', 'damaged item', 'defective', 'report complaint', 'file complaint'],
        'response': (
            "📌 **How to Report a Damaged / Defective Product:**\n\n"
            "1. Navigate to **File Grievance** (top navigation bar).\n"
            "2. **Section 1:** Enter your Product Name, select Category (e.g., *Home Appliance*, *Electronics*), Seller Name, Purchase Date, and Invoice Amount.\n"
            "3. **Section 2:** Under Complaint Type, select **'Damaged Product'** or **'Defective Product'**, choose your Priority, and pick your desired remedy (*Refund* or *Replacement*).\n"
            "4. **Section 3:** Drag and drop your **Purchase Invoice** and **photos of the physical damage**.\n"
            "5. Click **Register Complaint**. You will receive an instant unique Reference ID (e.g. `CMP-2026-000197`) to track investigation!"
        )
    },
    'track_complaint': {
        'triggers': ['how to track', 'track complaint', 'check status', 'where is my complaint', 'tracking'],
        'response': (
            "🔍 **How to Track Your Complaint:**\n\n"
            "• **Without Logging In:** Go to **Track Status** in the top menu or on the homepage, enter your Complaint ID (e.g. `CMP-2026-000197`), and click **Track Status**.\n"
            "• **From Consumer Dashboard:** Log in to view your complete case dossier, live 5-stage progress stepper, and official Authority responses."
        )
    },
    'under_review': {
        'triggers': ['under review', 'what does under review mean', 'review status'],
        'response': (
            "⏱️ **What Does 'Under Review' Mean?**\n\n"
            "Your grievance has passed initial intake scrutiny and is actively assigned to a **Grievance Redressal Officer**. "
            "The officer is currently evaluating your purchase invoice, verifying seller details, and serving an official inquiry notice to the merchant."
        )
    },
    'upload_evidence': {
        'triggers': ['upload evidence', 'how to upload', 'upload invoice', 'attachment', 'supporting proof', 'documents'],
        'response': (
            "📎 **How to Upload Evidence & Supported Documents:**\n\n"
            "• **Supported Formats:** PDF, JPG, PNG, WEBP (Up to 10MB).\n"
            "• **Recommended Proofs:** GST Tax Invoice, Online Order Receipt, Delivery Slip, Warranty Card, or Photos/Videos of the defect.\n"
            "• **How to Attach:** In the registration form (Section 3), click the dashed dropzone or drag your files directly into the box. A live preview will appear before submission."
        )
    },
    'after_submission': {
        'triggers': ['after submission', 'what happens next', 'what happens after', 'next steps'],
        'response': (
            "⚖️ **What Happens After You Submit a Complaint:**\n\n"
            "1. **Registration:** Your unique tracking code is generated immediately.\n"
            "2. **Officer Scrutiny:** An officer reviews your claim within the statutory SLA window.\n"
            "3. **Merchant Notice:** The seller/provider is summoned to inspect or reply.\n"
            "4. **Binding Resolution:** You receive an official redressal order with full refund, replacement, or repair instructions."
        )
    },
    'sla_timeline': {
        'triggers': ['sla', 'timeframe', 'how long', 'deadline', 'escalation', 'response time', 'delay'],
        'response': (
            "⏰ **Statutory SLA & Response Timelines:**\n\n"
            "Every grievance is protected by our automated SLA monitoring system:\n"
            "• **High Priority:** 24-hour response guarantee.\n"
            "• **Medium Priority:** 48-hour response guarantee.\n"
            "• **Low Priority:** 72-hour response guarantee.\n\n"
            "If an officer does not respond within this window, the system automatically flags an **SLA BREACH** and escalates the case to the Senior Redressal Authority!"
        )
    },
    'refund_resolutions': {
        'triggers': ['refund', 'replacement', 'remedy', 'resolutions', 'compensation', 'what can i get'],
        'response': (
            "💰 **Remedies You Can Seek:**\n\n"
            "Under the Consumer Protection Act, you can request:\n"
            "• **Full / Partial Refund:** Direct return of payment to your source account.\n"
            "• **Free Replacement:** Brand-new unit delivery with fresh warranty.\n"
            "• **Authorized Repair:** Free technician inspection and parts replacement.\n"
            "• **Damage Compensation:** For mental agony, transport, or service downtime."
        )
    }
}


def get_ai_assistant_response(user_message):
    """
    Processes user message and returns conversational guidance or real-time database lookup.
    """
    cleaned = user_message.strip()
    lower_msg = cleaned.lower()

    # 1. Check if user provided a Complaint ID to lookup (e.g. CMP-2026-000197)
    match = re.search(r'\bCMP-\d{4}-\w+\b', cleaned, re.IGNORECASE)
    if match:
        cid = match.group(0).upper()
        try:
            c = Complaint.objects.get(complaint_id__iexact=cid)
            response_text = (
                f"📋 **Live Status for {c.complaint_id}:**\n\n"
                f"• **Product:** {c.product_name}\n"
                f"• **Seller:** {c.seller}\n"
                f"• **Current Status:** `{c.status}`\n"
                f"• **Priority:** {c.priority}\n"
                f"• **SLA Timeline:** {c.sla_time_display}\n"
                f"• **Registered On:** {c.created_at.strftime('%d %B %Y, %H:%M')}\n\n"
            )
            if c.admin_response:
                response_text += f"⚖️ **Latest Authority Order:**\n> {c.admin_response}\n\n"
            else:
                response_text += "ℹ️ *Case is currently under active officer inquiry. Formal orders will appear once merchant examination concludes.*\n\n"
            response_text += f"[👉 Click here to view complete Case Dossier](/complaints/{c.complaint_id}/)"
            return response_text
        except Complaint.DoesNotExist:
            return f"⚠️ I searched our national registry but could not find a complaint matching ID **{cid}**. Please check for typos and try again."

    # 2. Check FAQ Knowledge Base triggers
    for key, data in FAQ_KNOWLEDGE_BASE.items():
        if any(trigger in lower_msg for trigger in data['triggers']):
            return data['response']

    # 3. Smart Category / Recommendation if user describes an item/problem
    categories_detection = {
        'mobile': ('Mobile & Computers', 'Defective Product', 'Replacement'),
        'phone': ('Mobile & Computers', 'Defective Product', 'Replacement'),
        'laptop': ('Mobile & Computers', 'Warranty Issue', 'Repair'),
        'washing machine': ('Home Appliance', 'Damaged Product', 'Replacement or Refund'),
        'refrigerator': ('Home Appliance', 'Defective Product', 'Repair or Replacement'),
        'tv': ('Home Appliance', 'Defective Product', 'Replacement'),
        'broadband': ('Internet & Telecom', 'Service Issue', 'Compensation or Bill Rebate'),
        'wifi': ('Internet & Telecom', 'Service Issue', 'Compensation'),
        'courier': ('Delivery & Logistics', 'Product Not Delivered', 'Full Refund'),
        'delivery': ('Delivery & Logistics', 'Late Delivery', 'Refund'),
        'shoes': ('Fashion & Clothing', 'Wrong Product', 'Replacement'),
        'clothes': ('Fashion & Clothing', 'Poor Quality', 'Refund'),
        'sofa': ('Furniture', 'Poor Quality', 'Repair or Replacement'),
        'flight': ('Travel & Transport', 'Refund Issue', 'Full Refund'),
        'train': ('Travel & Transport', 'Refund Issue', 'Full Refund'),
    }

    for keyword, (cat, ctype, remedy) in categories_detection.items():
        if keyword in lower_msg:
            return (
                f"💡 **Recommended Filing Details for your issue with '{keyword.title()}':**\n\n"
                f"• **Sector / Category:** `{cat}`\n"
                f"• **Complaint Type:** `{ctype}`\n"
                f"• **Recommended Remedy:** `{remedy}`\n\n"
                f"Would you like to register this now? Head over to **File Grievance** to submit with your invoice proof!"
            )

    # 4. Fallback greeting & guided prompts
    return (
        "👋 Hello! I am your **ConsumerCare Redressal Assistant**.\n\n"
        "I can assist you with:\n"
        "• **Filing a Complaint:** Ask *'How do I report a damaged product?'*\n"
        "• **Live Tracking:** Type any Complaint ID like *'Status of CMP-2026-000197'*\n"
        "• **Inquiry Stages:** Ask *'What does Under Review mean?'*\n"
        "• **SLA Response Deadlines:** Ask *'How long does resolution take?'*\n"
        "• **Evidence Uploads:** Ask *'How do I upload an invoice?'*\n\n"
        "How can I help you protect your consumer rights today?"
    )
