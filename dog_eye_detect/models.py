from django.db import models
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_delete


class XceptionImage(models.Model):
    file = models.FileField(null=True, blank=True, unique=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    path = models.FilePathField(path=settings.MEDIA_ROOT, default=settings.MEDIA_ROOT)
    id = models.BigAutoField(primary_key=True)

    class Meta:	
        unique_together = ['file', 'path']	


@receiver(post_delete, sender=XceptionImage)
def submission_delete(sender, instance, **kwargs):
    """
    파일 삭제 요청보내면 저장된 파일만 지우는 게 아니라 db 에 저장된 정보도 삭제해줌.
    삭제 요청 보내면 장고는 그냥 파일만 지우고, 기록은 안 지워줌.
    """
    instance.file.delete(False)