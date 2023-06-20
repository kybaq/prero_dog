from django.forms import ModelForm
from dog_eye_detect.models import XceptionImage


class FileForm(ModelForm):
    """
    Creating a form that maps to the model: https://docs.djangoproject.com/en/2.2/topics/forms/modelforms/
    This form is used for the file upload.
    """
    class Meta:
        model = XceptionImage
        fields = ['file']