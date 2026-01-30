from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
    full_name = forms.CharField(max_length=200, required=True)
    email = forms.EmailField(required=True)
    confirm_email = forms.EmailField(label='Confirm Email', required=True)
    
    # Crypto addresses (optional)
    bitcoin_address = forms.CharField(max_length=100, required=False, label='Bitcoin Address')
    ethereum_address = forms.CharField(max_length=100, required=False, label='Ethereum Address')
    trx_address = forms.CharField(max_length=100, required=False, label='TRX Address')
    usdt_address = forms.CharField(max_length=100, required=False, label='USDT Address')
    
    class Meta:
        model = User
        fields = ['full_name', 'username', 'email', 'confirm_email', 
                  'password1', 'password2',
                  'bitcoin_address', 'ethereum_address', 'trx_address', 'usdt_address']
    
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        confirm_email = cleaned_data.get('confirm_email')
        
        if email and confirm_email and email != confirm_email:
            raise forms.ValidationError("Emails do not match")
        
        return cleaned_data