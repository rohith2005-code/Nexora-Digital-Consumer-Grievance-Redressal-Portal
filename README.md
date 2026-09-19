# Digital Consumer Complaint Registration & Grievance Redressal System

An end-to-end full-stack web application designed for consumers to register grievances against defective products, unfair trade practices, or deficient services, upload purchase and photo evidence, track real-time redressal progress via an animated progress stepper, and receive binding resolutions from designated grievance redressal authorities.

Developed based on the **Entri Learning Journey** curriculum:
`Python → Django → Django ORM → Authentication → Role-Based Access → Media Handling → Django REST Framework → Full-Stack Integration → Grievance System`.

---

## 🎯 Project Objective

To provide a centralized digital platform where consumers can register complaints related to products or services, submit relevant purchase and evidence information, track complaint status, and receive responses/resolutions from the responsible authority or administrator.

> **Note for Mentor / Evaluator**: This is a digital grievance platform inspired by consumer complaint processes, not an official Consumer Court.

---

## 🏗️ Architecture & Technology Stack

| Area | Technologies |
| :--- | :--- |
| **Programming Language** | Python 3.10+, JavaScript (ES6+) |
| **Backend Framework** | Django 4.2 |
| **API Framework** | Django REST Framework (DRF) |
| **Database** | SQLite3 via Django ORM (Migrations, ForeignKeys) |
| **Authentication** | Django Auth System with `is_staff` Role-Based Access Control |
| **File / Media Handling** | Django `FileField` / `ImageField`, Pillow, Media serving |
| **Frontend UI** | HTML5, CSS3 Custom Modern Design System, Glassmorphism, CSS Keyframe Animations |
| **Icons & Typography** | FontAwesome 6, Plus Jakarta Sans |
| **Testing** | Django Automated Test Framework (`django.test.TestCase`) |

---

## 🔄 Redressal Workflow & Flowchart

```
Consumer Complaint Registration System
                ↓
            Consumer
                ↓
       Select/Add Product
                ↓
       Enter Complaint Details
                ↓
       Upload Supporting Proof (Bill/Invoice/Photos)
                ↓
       Submit Complaint (Auto ID: CMP-2026-XXXXX)
                ↓
        Complaint Tracking
                ↓
      Authority/Admin Review
                ↓
        Status / Response
                ↓
           Resolution
```

---

## 👥 Role-Based Access & Dashboards

The system separates standard consumers from grievance redressal officers using Django's built-in `is_staff` property:

```
Login → is_staff=True  → Grievance Authority / Admin Portal
Login → is_staff=False → Consumer Dashboard
```

### 1. Consumer Portal (`is_staff = False`)
- **Consumer Dashboard**: Personal complaint statistics (Total, Submitted, Under Review, Resolved), search bar, and filter tabs (All, Active, Resolved).
- **Complaint Registration**:
  - Auto-generated tracking code in format `CMP-YYYY-XXXXX`.
  - Product/Service name, Category selection, Seller/Manufacturer, Purchase Date, Amount Paid (₹).
  - Complaint Type (12 options: Defective Product, Damaged Product, Wrong Product, Late Delivery, Overcharging, Warranty Issue, etc.).
  - Expected Resolution (Refund, Replacement, Repair, Delivery, Warranty Service, Compensation).
  - Priority selector (Low, Medium, High).
  - Detailed Description with live character counter.
  - Drag-and-drop evidence dropzone with live preview for receipts, invoices, and product damage photos.
- **Complaint Tracking & Details**:
  - Animated 5-stage progress stepper:
    `Submitted` ➔ `Under Review` ➔ `In Progress` ➔ `Resolved` ➔ `Closed`
  - Alert state for `Additional Information Required` with an interactive form allowing the consumer to submit requested clarifications or extra proofs.
  - Timeline audit history showing who took what action and when.

### 2. Grievance Authority / Admin Portal (`is_staff = True`)
- **Authority Command Center**:
  - Real-time grievance metric cards: Total Filed, Submitted, Under Review, Additional Info Needed, In Progress, Resolved, Closed.
  - Multi-criteria filter: Filter by Status, Priority, and Category simultaneously.
  - Live search by Complaint ID, Consumer Name, or Product.
  - **Export CSV Report**: Download official grievance records for compliance and reporting.
- **Adjudication & Review Interface**:
  - Split screen view: Consumer profile, purchase data, consumer statement, and attached evidence on the left.
  - Decision form on the right: Update status, adjust priority, record internal investigation notes, and publish official binding response/resolution text visible to the consumer.

### 3. Public Quick Tracker
- Unauthenticated consumers or third parties can check real-time progress of any valid Complaint ID directly from the homepage or `/track/` page without logging in.

---

## 📡 REST API Endpoints (Django REST Framework)

| Method | Endpoint | Description | Access |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/complaints/` | List complaints (user's own or all if staff) | Authenticated |
| `POST` | `/api/complaints/` | Register new complaint via JSON | Authenticated |
| `GET` | `/api/complaints/<id>/` | Retrieve specific complaint details | Authenticated |
| `GET` | `/api/track/<complaint_id>/` | Public tracking lookup by Complaint ID | Public |
| `GET` | `/api/stats/` | System-wide grievance statistics | Public |

---

## 🔑 Default Test Accounts (Pre-Seeded)

| Role | Username | Password | Access Level |
| :--- | :--- | :--- | :--- |
| **Grievance Officer (Admin)** | `officer_admin` | `adminpass123` | `is_staff = True` (Authority Portal) |
| **Consumer 1** | `rahul_consumer` | `consumerpass123` | `is_staff = False` (Consumer Portal) |
| **Consumer 2** | `priya_consumer` | `consumerpass123` | `is_staff = False` (Consumer Portal) |

---

## 🚀 How to Run the Project

### Option A: One-Click Launch (Windows)
Double-click `start_system.bat` or run:
```powershell
.\start_system.bat
```

### Option B: Manual Terminal Execution
```powershell
cd consumer_complaint_system

# 1. Apply Migrations
python manage.py makemigrations
python manage.py migrate

# 2. Seed Realistic Demo Data
python seed_data.py

# 3. Run Automated Tests
python manage.py test complaints

# 4. Start Development Server
python manage.py runserver 8000
```
Then open your browser at **`http://127.0.0.1:8000/`**.

---

## 🎤 Viva / Mentor Questions & Answers

**Q1: Why did you transition from an e-commerce support ticket system to this Consumer Grievance System?**
> *Answer:* An e-commerce support ticket only handles inquiries for one specific store. Based on mentor feedback, I broadened the project into a centralized Digital Consumer Complaint Registration & Grievance Redressal System that allows consumers to file grievances against *any* seller, manufacturer, or service provider (Samsung, Apple, Couriers, ISPs, etc.) across 12 distinct categories with evidence upload, priority triage, and an animated progress stepper.

**Q2: How is role-based access handled in Django?**
> *Answer:* Rather than hardcoding usernames, role-based access uses Django's native `user.is_staff` property. Upon authentication, the `login_redirect` view inspects `request.user.is_staff`: if `True`, the user is routed to the Authority Adjudication Portal; if `False`, to the Consumer Dashboard. Protected views use the `@user_passes_test(staff_check)` decorator.

**Q3: How are unique Complaint IDs generated?**
> *Answer:* In `complaints/models.py`, the `Complaint` model overrides the `save()` method. If `complaint_id` is empty, it combines the current calendar year, a zero-padded sequential counter, and a random salt (e.g. `CMP-2026-000184`), and verifies uniqueness against the database before saving.

**Q4: How does the system handle supporting evidence and media files?**
> *Answer:* The model utilizes `FileField(upload_to='complaint_evidence/')`. In `settings.py`, `MEDIA_ROOT` and `MEDIA_URL` are configured, with files stored securely on disk and served during development via `static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)`. The frontend features a drag-and-drop zone with client-side image preview and format validation.
