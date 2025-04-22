from django import forms
from .models import ShippingAddress

class ShippingAddressForm(forms.ModelForm):
    full_name = forms.CharField()
    email = forms.CharField()
    phone = forms.CharField()
    address1 = forms.CharField()
    address2 = forms.CharField()
    city = forms.CharField()
    state = forms.CharField()
    zipcode = forms.CharField()
    country = forms.CharField()

    class Meta:
        model = ShippingAddress
        fields = ["full_name", "email", "phone", "address1", "address2", "city", "state", "zipcode", "country", 'primary']