import os
import cv2
from os import listdir
from os.path import join
from os.path import isfile
from ultralytics import YOLO
from googlesearch import search
from django.conf import settings
from django.shortcuts import render
from rest_framework import views, status
from django.views.generic import ListView
from rest_framework.response import Response
from django.views.generic import TemplateView
from rest_framework.parsers import FormParser
from django.views.generic.edit import CreateView
from rest_framework.parsers import MultiPartParser
from django.core.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.renderers import TemplateHTMLRenderer


from dog_skin_detect.models import YoloImage
from dog_skin_detect.serializes import FileSerializer
from django.db import IntegrityError
from django.contrib import messages


class IndexView(TemplateView):
    """
    웹 사이트 render view.
    """
    template_name = 'dog_skin_detect/skin_detection.html'

    

class FilesList(ListView):
    """
    :param model: 어떤 모델 구조를 가진 파일을 불러올 것인지 유형을 정함(내 모델 가지고 오기)
    :param template_name; 
    :param context_object_name: Custom defined context object value,
                     this can override default context object value.
    """
    model = YoloImage
    template_name = 'dog_skin_detect/files_list.html'
    context_object_name = 'files_list'

    def show_files_list(request):
        files_list = YoloImage.objects.all()
        return render(request, 'dog_skin_detect/skin_detection.html', {'files_list': files_list})



class UploadView(CreateView):
    model = YoloImage
    fields = ['file']
    template_name = 'dog_skin_detect/post_file.html'
    success_url = 'upload_success/'

    def form_valid(self, form):
        file = form.instance.file
        path = form.instance.path
        try:
            if YoloImage.objects.filter(file=file.name, path=path).exists():
                form.add_error('file', ValidationError('이미 예측을 진행한 사진입니다!'))
                return super().form_invalid(form)
            else:
                return super().form_valid(form)
            
        except IntegrityError:
            messages.error(self.request, 'A database error occurred.')
            return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['view_mode'] = 'upload'  # Set the view_mode here
        context['files_list'] = YoloImage.objects.all()
        return context



class UploadSuccessView(TemplateView):
    """
    업로드 성공적으로 되면 출력해줄 페이지. 템플릿 상속 페이지임.
    """
    template_name = 'dog_skin_detect/upload_success.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['view_mode'] = 'success'  # Set the view_mode here
        context['files_list'] = YoloImage.objects.all()
        return context



class SelectPredFileView(TemplateView):
    """
    서버에 업로드된 파일을 확인하는 view.
    """

    template_name = 'dog_skin_detect/select_file_predictions.html'
    parser_classes = FormParser
    queryset = YoloImage.objects.all()

    def get_context_data(self, **kwargs):
        """
        MEDIA_ROOT 에 있는 파일들의 정보를 가져옴.
        """
        context = super().get_context_data(**kwargs)
        media_path = settings.MEDIA_ROOT
        myfiles = [f for f in listdir(media_path) if isfile(join(media_path, f))]
        context['filename'] = myfiles
        return context


class SelectFileDelView(TemplateView):
    """
    서버에 업로드된 파일들을 불러옴.
    그 뒤 삭제할 수 있도록.
    이 때, 모델과 맞지 않는 파일일 경우 삭제할 권한이 없다
    """
    template_name = "dog_skin_detect/select_file_deletion.html"
    parser_classes = FormParser
    queryset = YoloImage.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        media_path = settings.MEDIA_ROOT
        myfiles = [f for f in listdir(media_path) if isfile(join(media_path, f))]
        primary_key_list = []
        for value in myfiles:
            primary_key = YoloImage.objects.filter(file=value).values_list("pk", flat=True)
            if primary_key.exists():  # Check if the queryset is not empty
                primary_key_list.append(primary_key.first())  # .first() will get the first (and only) value from the queryset
            else:
                primary_key_list.append(None)  # Append None if no primary key exists

        file_and_pk = list(zip(myfiles, primary_key_list))
        context["filename"] = file_and_pk
        return context



class FileDeleteView(views.APIView):
    """
    파일 삭제 API 에게 post 요청을 보내 파일 삭제함
    """
    model = YoloImage
    fields = ['file']
    template_name = "dog_skin_detect/select_file_deletion.html"
    success_url = '/delete_success/'

    def post(self, request, pk): # primary key 사용
        """
        파일 실제로 삭제 요청 보냄
        """
        delete_action = get_object_or_404(YoloImage, pk=pk).delete()  # Use 'pk' directly
        try:
            # 정상적으로 삭제되면 안내 표시 해줌
            return render(request, 'dog_skin_detect/delete_success.html', {'pk': delete_action})
        except ValueError as err:
            return Response(str(err), status=status.HTTP_400_BAD_REQUEST)



class FileView(views.APIView):
    """
    API 에 post 요청으로 파일 업로드 하는 view
    """
    parser_classes = (MultiPartParser, FormParser)
    queryset = YoloImage.objects.all()

    # def post(request):
    #     """
    #     post 요청 보냄
    #     """
    #     file_serializer = FileSerializer(data=request.data)
    #     if file_serializer.is_valid():
    #         file_serializer.save()
    #         response = Response(file_serializer.data, status=status.HTTP_201_CREATED)
    #     else:
    #         response = Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    #     return response

    # API 페이지로 이동하지 않게 만듦
    # @staticmethod
    def post(self, request):
        file_name = request.data.get('file').name  # Extract file name
        if self.check_file_exists(file_name) or self.check_object_exists(file_name):
            return Response({"error": "File already exists"}, status=status.HTTP_400_BAD_REQUEST)

        file_serializer = FileSerializer(data=request.data)

        ## 업로드 후 API site 나오는 건 여기 response 를 httpsResponse 로 바꿔서 render 해주면 될듯?
        """
        if file_serializer.is_valid():
            file_serializer.save()
            return Response(file_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        """

        if file_serializer.is_valid():
            file_serializer.save()
            # return HttpResponseRedirect(reverse('upload_success'))
            return render(request, 'dog_skin_detect/upload_success.html')
        
        else:
            return Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # @staticmethod
    def check_file_exists(self, file_name):
        """
        This method will receive as input the file the user wants to store
        on the server and check if a file with this name is physically in
        the server folder.
        If this function returns True, the user should not be able to save the
        file (or at least he/she should be prompted with a message saying that
        the file is already existing)
        """
        check = os.path.isfile(os.path.join(settings.MEDIA_ROOT, file_name))
        return check

    # @staticmethod
    def check_object_exists(self, file_name):
        """
        This method will receive as input the file the user wants to store
        on the server and check if an object with that name exists in the
        database.
        If this function returns True, the user should not be able to save the
        file (or at least he/she should be prompted with a message saying that
        the file is already existing)
        """
        check = YoloImage.objects.filter(file=file_name).exists()
        return check
    

class Skin_Predict(views.APIView):
    """
    학습한 모델의 가중치를 불러오고 예측을 진행하는 코드, rest framework 를 이용해서 yolov8 api 를 만듦.
    """

    template_name = 'dog_skin_detect/skin_detection.html'
    renderer_classes = [TemplateHTMLRenderer]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Load your YOLOv8 model here
        self.model = YOLO("/Users/csb01/Desktop/best.pt")

    def post(self, request):
        """
        FileView 클래스에서 업로드한 파일들 목록을 확인할 수 있음
        """
        filename = request.POST.getlist('file_name').pop()
        filepath = str(os.path.join(settings.MEDIA_ROOT, filename))

        # 파일 선택 후 실제로 예측 수행함
        results = self.model(filepath)
        
        # 결과 가져옴
        plotted_result = results[0].plot()
        # 파일 저장 경로 가져옴
        output_directory = os.path.join(settings.MEDIA_ROOT, 'predicted_images')

        # dir 새로 필요하면 만듦. 
        os.makedirs(output_directory, exist_ok=True)

        output_filename = "output_" + filename
        output_filepath = os.path.join(output_directory, output_filename)

        # 파일 저장
        cv2.imwrite(output_filepath, plotted_result)

        # 위에서 예측을 통해 모델에서 반환된 이미지를 다시 출력해주기 위해 파일 경로 가져옴
        output_image_url = output_filepath.replace(settings.MEDIA_ROOT, '/media/')

        # 예측 후 구글 웹 크롤링으로 검색함
        search_query = '반려견 피부 영양제' # yolo 에서 class 추출이 어려워서 검색어 일괄 적용
        search_results = search(search_query, num_results=1)

        # render 함수 반환해 템플릿 상속받은 페이지 보여주기
        return render(request, 'dog_skin_detect/display_output.html', {'image_url': output_image_url, 'search_results': search_results})

        ####(debug 용 API)
        # return Response({'output_image': output_filepath}, status=status.HTTP_200_OK)
