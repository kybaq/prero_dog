from django.forms import ModelForm
from dog_skin_detect.models import YoloImage


class FileForm(ModelForm):
    """
    Creating a form that maps to the model: https://docs.djangoproject.com/en/2.2/topics/forms/modelforms/
    This form is used for the file upload.
    """
    class Meta:
        model = YoloImage
        fields = ['file']