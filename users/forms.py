from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm
from django import forms
from .models import CustomUser, BillingAddress


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ("email",)


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ("email",)


class CustomUserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2')

class UpdateUserForm(UserChangeForm):
    password = None

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email']


class UpdateUserPassword(PasswordChangeForm):
    class Meta:
        model = CustomUser
        fields = ['new_password1', 'new_password2']

import os

class UserProfileImageForm(forms.ModelForm):
    profile_image = forms.ImageField(required=False)

    class Meta:
        model = CustomUser
        fields = ["profile_image"]

    def save(self, commit=True):
        user = super().save(commit=False)

        if 'profile_image' in self.changed_data:
            try:
                old_image = CustomUser.objects.get(pk=user.pk).profile_image
                if old_image and old_image != user.profile_image:
                    old_path = old_image.path
                    if os.path.exists(old_path):
                        os.remove(old_path)
            except CustomUser.DoesNotExist:
                pass

        if commit:
            user.save()
        return user


class UpdatedBillingAddressForm(forms.ModelForm):
    full_name = forms.CharField(disabled=True)  # Optional: disable editing
    email = forms.EmailField(disabled=True)     # Optional: disable editing
    phone = forms.CharField()
    address1 = forms.CharField()
    address2 = forms.CharField(required=False)
    city = forms.CharField()
    state = forms.CharField(required=False)
    zipcode = forms.CharField()
    country = forms.CharField()

    class Meta:
        model = BillingAddress
        fields = ["full_name", "email", "phone", "address1", "address2", "city", "state", "zipcode", "country"]



        
