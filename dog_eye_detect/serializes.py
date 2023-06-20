from rest_framework import serializers
from .models import XceptionImage


class FileSerializer(serializers.ModelSerializer):

    class Meta:
        model = XceptionImage
        fields = ('file', 'timestamp')