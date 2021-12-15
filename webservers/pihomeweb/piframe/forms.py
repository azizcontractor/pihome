from io import BytesIO

from django import forms
from .models import Slide


class UploadForm(forms.ModelForm):
    error_css_class = "w3-red w3-ul"

    class Meta:
        model = Slide
        fields = ["title", "image"]
        widgets = {"title": forms.TextInput(attrs={"class": "w3-input"})}
