from django import forms
from django.contrib.auth.models import User
from .models import Complaint, ComplaintTimeline


class ConsumerRegistrationForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Create Password'}),
        min_length=6
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}),
        min_length=6
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose Username'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already taken. Please choose another.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        pwd = cleaned_data.get('password')
        confirm_pwd = cleaned_data.get('confirm_password')
        if pwd and confirm_pwd and pwd != confirm_pwd:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data


class ComplaintRegistrationForm(forms.ModelForm):
    purchase_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        })
    )

    class Meta:
        model = Complaint
        fields = [
            'product_name',
            'category',
            'seller',
            'purchase_date',
            'amount_paid',
            'complaint_type',
            'priority',
            'expected_resolution',
            'description',
            'attachment',
        ]
        widgets = {
            'product_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Samsung Galaxy S23 / LG Smart TV / Urban Ladder Sofa',
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'seller': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Amazon India / Croma / XYZ Retail Store',
            }),
            'amount_paid': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Amount in ₹ (e.g. 24999.00)',
                'step': '0.01',
            }),
            'complaint_type': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'expected_resolution': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe the issue clearly: what happened, defects noticed, previous communications with seller, etc.',
            }),
            'attachment': forms.ClearableFileInput(attrs={
                'class': 'form-control-file',
                'id': 'fileUploadInput',
            }),
        }


class AdminComplaintReviewForm(forms.ModelForm):
    internal_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Optional internal investigation note or update reason (logged in audit timeline)',
        })
    )

    class Meta:
        model = Complaint
        fields = ['status', 'priority', 'admin_response']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'admin_response': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Enter official resolution, findings, compensation instructions, or request for additional info visible to consumer...',
            }),
        }


class ConsumerAdditionalInfoForm(forms.Form):
    additional_remarks = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Provide the requested details, clarification, or follow-up statement...',
        })
    )
    new_attachment = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'})
    )
