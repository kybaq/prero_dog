from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from dog_skin_detect.views import FilesList,FileView, FileDeleteView, IndexView, Skin_Predict
from dog_skin_detect.views import SelectPredFileView, SelectFileDelView, FileDeleteView, UploadView , UploadSuccessView

app_name = 'dog_skin_detect'

urlpatterns = [
    path('', IndexView.as_view(), name='IndexView'),
    path('predict/', Skin_Predict.as_view(), name='APIpredict'),
    path('upload/', FileView.as_view(), name='APIupload'),
    path('delete/<int:pk>/', FileDeleteView.as_view(), name='APIdelete'),
        # Url to list all the files in the server
    path('files_list/', FilesList.as_view(), name='files_list'),
    path('filedelete/', SelectFileDelView.as_view(), name='file_delete'),
    path('delete_success/', FileDeleteView.as_view(), name='delete_success'),
    path('fileupload/', UploadView.as_view(), name='upload_file'),
    # Url to select a file for the predictions
    path('fileselect/', SelectPredFileView.as_view(), name='file_select'),
    # Url to select a file to be deleted and confirm the upload
    path('upload_success/', UploadSuccessView.as_view(), name='upload_success'),
    # path('display_image/<str:image_url>', views.display_image, name='display_image'),
    path('bulletin/', include('bulletin.urls', namespace='bulletin')),
        # Urls to upload the file and confirm the upload

]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)