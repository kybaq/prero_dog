from rest_framework import serializers
from .models import YoloImage


class FileSerializer(serializers.ModelSerializer):

    class Meta:
        model = YoloImage
        fields = ('file', 'timestamp')