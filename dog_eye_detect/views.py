import os
import requests
import numpy as np
from os import listdir
from os.path import join
from os.path import isfile
from googlesearch import search
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponseRedirect
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
from django.urls import reverse
from bs4 import BeautifulSoup
from dog_eye_detect.models import XceptionImage
from dog_eye_detect.serializes import FileSerializer
from django.db import IntegrityError
from django.contrib import messages

import keras
from keras.utils import load_img
from keras.utils import img_to_array
from keras.models import load_model

class IndexView(TemplateView):
    """
    웹 사이트 render view.
    """
    template_name = "dog_eye_detect/eye_detection.html"

    

class FilesList(ListView):
    """
    업로드한 파일을 확인할 수 있는 view.
    """
    model = XceptionImage
    template_name = "dog_eye_detect/files_list.html"
    context_object_name = "files_list"

    def show_files_list(request):
        files_list = XceptionImage.objects.all()
        return render(request, "dog_eye_detect/eye_detection.html", {"files_list": files_list})



class UploadView(CreateView):
    """
    파일을 서버에 업로드하는 view.
    """
    model = XceptionImage
    fields = ["file"]
    template_name = "dog_eye_detect/post_file.html"
    success_url = "upload_success/"

    def form_valid(self, form):
        file = form.instance.file
        path = form.instance.path
        try:
            if XceptionImage.objects.filter(file=file.name, path=path).exists():
                form.add_error("file", ValidationError("이미 업로드한 사진입니다!"))
                return super().form_invalid(form)
            else:
                return super().form_valid(form)
        except IntegrityError:
            messages.error(self.request, "A database error occurred.")
            return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["view_mode"] = "upload"  # Set the view_mode here
        context["files_list"] = XceptionImage.objects.all()
        return context



class UploadSuccessView(TemplateView):
    """
    업로드후 
    """
    template_name = "dog_eye_detect/upload_success.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["view_mode"] = "success"  # Set the view_mode here
        context["files_list"] = XceptionImage.objects.all()
        return context



class SelectPredFileView(TemplateView):
    """
    This view is used to select a file from the list of files in the server.
    After the selection, it will send the file to the server.
    The server will return the predictions.
    """

    template_name = "dog_eye_detect/select_file_predictions.html"
    parser_classes = FormParser
    queryset = XceptionImage.objects.all()

    def get_context_data(self, **kwargs):
        """
        This function is used to render the list of files in the MEDIA_ROOT in the html template.
        """
        context = super().get_context_data(**kwargs)
        media_path = settings.MEDIA_ROOT
        myfiles = [f for f in listdir(media_path) if isfile(join(media_path, f))]
        context["filename"] = myfiles
        return context



class SelectFileDelView(TemplateView):
    """
    This view is used to select a file from the list of files in the server.
    After the selection, it will send the file to the server.
    The server will then delete the file.
    """
    template_name = "dog_eye_detect/select_file_deletion.html"
    parser_classes = FormParser
    queryset = XceptionImage.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        media_path = settings.MEDIA_ROOT
        myfiles = [f for f in listdir(media_path) if isfile(join(media_path, f))]
        primary_key_list = []
        for value in myfiles:
            primary_key = XceptionImage.objects.filter(file=value).values_list("pk", flat=True)
            if primary_key.exists():  # Check if the queryset is not empty
                primary_key_list.append(primary_key.first())  # .first() will get the first (and only) value from the queryset
            else:
                primary_key_list.append(None)  # Append None if no primary key exists

        file_and_pk = list(zip(myfiles, primary_key_list))
        context["filename"] = file_and_pk
        return context



class FileDeleteView(views.APIView):
    """
    This class contains the method to delete a file interacting directly with the API.
    DELETE requests are accepted.
    """
    model = XceptionImage
    fields = ['file']
    template_name = "dog_eye_detect/select_file_deletion.html"
    success_url = '/delete_success/'

    def post(self, request, pk):   # Add 'pk' as an argument
        """
        This method is used delete a file.
        """
        delete_action = get_object_or_404(XceptionImage, pk=pk).delete()  # Use 'pk' directly
        try:
            # after successful delete, render a success page
            return render(request, 'dog_eye_detect/delete_success.html', {'pk': delete_action})
        except ValueError as err:
            return Response(str(err), status=status.HTTP_400_BAD_REQUEST)




class FileView(views.APIView):
    """
    This class contains the method to upload a file interacting directly with the API.
    POST requests are accepted.
    """
    parser_classes = (MultiPartParser, FormParser)
    queryset = XceptionImage.objects.all()

    # def post(request):
    #     """
    #     This method is used to Make POST requests to save a file in the media folder
    #     """
    #     file_serializer = FileSerializer(data=request.data)
    #     if file_serializer.is_valid():
    #         file_serializer.save()
    #         response = Response(file_serializer.data, status=status.HTTP_201_CREATED)
    #     else:
    #         response = Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    #     return response


    # @staticmethod
    def post(self, request):
        file_name = request.data.get("file").name  # Extract file name
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
            return HttpResponseRedirect(reverse("dog_eye_detect:upload_success"))
        
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
        check = XceptionImage.objects.filter(file=file_name).exists()
        return check


def search(query, num_results):
    search_url = f"https://www.google.com/search?q={query}&num={num_results}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    search_results = []

    for result in soup.find_all("div", class_="yuRUbf"):
        link = result.find("a")
        url = link["href"]
        search_results.append(url)

    return search_results

class Eye_Predict(views.APIView):
    """
    학습한 모델의 가중치를 불러오고 예측을 진행하는 코드, rest framework 를 이용해서 yolov8 api 를 만듦.
    """

    template_name = "dog_eye_detect/eye_detection.html"
    renderer_classes = [TemplateHTMLRenderer]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Load your model here
        self.model = load_model("/Users/csb01/Desktop/dog_eye_disease_xception_epoch_100_true.h5")

    def post(self, request):
        """
        This method is used to make predictions on image files
        loaded with FileView.post
        """
        filename = request.POST.getlist("file_name").pop()
        filepath = str(os.path.join(settings.MEDIA_ROOT, filename))

        height = width = 224
        
        channel = 3

        test_image = np.zeros((1, height, width, channel))

        img = load_img(filepath, target_size=(height, width))
        img_tensor = img_to_array(img)
        img_tensor = np.array(img_tensor, dtype="float32")

        img_tensor /= 255

        img_tensor = np.expand_dims(img_tensor, axis=0)

        test_image[0] = img_tensor

        predictions = self.model.predict(test_image)

        def build_output(predictions):
            disease = np.argmax(predictions)
            
            # Update the conditions based on your model"s output
            if disease == 0:
                disease = "non ulcerative corneal disease"
                keyword = "비궤양성 각막질환"
            elif disease == 1:
                disease = "blepharitis"
                keyword = "안검염"
            elif disease == 2:
                disease = "blepharoncus"
                keyword = "안검종양"
            elif disease == 3:
                disease = "cataract"
                keyword = "백내장"
            elif disease == 4:
                disease = "conjunctivitis"
                keyword = "결막염"
            elif disease == 5:
                disease = "epiphora"
                keyword = "유루증"
            elif disease == 6:
                disease = "intraocular refractory"
                keyword = "안검내반증"
            elif disease == 7:
                disease = "normal"
                # 정상이라 별 검색어 추가 안 함
                keyword = ""
            elif disease == 8:
                disease = "nuclear sclerosis"
                keyword = "핵경화"
            elif disease == 9:
                disease = "pigmentary keratitis"
                keyword = "색소침착성 각막염"
            elif disease == 10:
                disease = "ulcerative corneal disease"
                keyword = "궤양성 각막질환"

            return disease, keyword
        
        disease, keyword = build_output(predictions)

        print("병",disease)

        search_query = "강아지" + keyword + "영양제"

        print("검색어", search_query)

        # Perform a search based on the predicted disease
        search_results = search(search_query, num_results=2)

        # Retrieve additional information for each search result
        search_result_details = []
        for result in search_results:
            try:
                response = requests.get(result)
                soup = BeautifulSoup(response.text, "html.parser")
                link = soup.select_one("#rso > div:nth-child(1) > div > div > div > div > a")
                website_name = link.get_text()
            except:
                website_name = "N/A"
            search_result_details.append({"url": result, "website_name": website_name})

        # Render the template with the search results
        return render(request, "dog_eye_detect/display_output.html", {"search_results": search_result_details})

"""
an_ulcerative_corneal_diseasse: 비궤양성 각막질환 -> 궤양까지는 안되는 질환
blepharitis: 안검염 -> 눈커풀 및 눈커풀 테두리의 염증
blepharoncus: 안검종양 -> 눈 및 쪽이나 눈커풀 쪽에 혹처럼 염증이 생김
cataract: 백내장 -> 수정체가 혼탁해져서 눈이 뿌옇게 되는 질환
conjunctivitis: 결막염 -> 결막에 염증이 생긴것.
epiphora: 유루증 -> 눈물이 계속나와서 눈물 자국이 생길 정도임.
intraocular_refractory: 안검내반증 -> 속눈썹이 안구 안쪽을 향해 자라면서 눈동자를 찌름
nuclear_sclerosis: 핵경화 -> 강아지가 노화되면서 수정체가 굳어가는 현상
pigmentary_keratitis: 색소침착성각막염 -> 눈에 멜라닌 색소가 침착해서 눈 표면이 짙은 갈색으로 변함.
ulcerative_corneal_disease: 궤양성 각막질환 -> 각막이 궤양될 수 있는 질환
Normal: 정상
"""