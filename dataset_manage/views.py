from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.forms import modelformset_factory
from .forms import BasicForm, AuthorForm, DatasetFileForm, AdditionalInfoForm, PhotoReviewForm, CommentForm
from .models import Dataset, Author, DatasetFile, AdditionalInfo, PhotoReview, DatasetView, Comment, DatasetRequest
from PIL import Image
import logging
from django.core.files.base import ContentFile
import base64
import os
import json
from django.http import JsonResponse
from django.utils import timezone
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import DatasetRequestSerializer
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout


logger = logging.getLogger(__name__)

class CustomLoginView(LoginView):
    template_name = 'login.html'
    success_url = '/dataset_manage/dataset/'

    def get_success_url(self):
        return self.success_url
    
def custom_logout_view(request):
    logout(request)
    return redirect('landing_page')

def landing_page_view(request):
    return render(request, 'landing_page.html')

def dataset_view(request):
    datasets = Dataset.objects.all().prefetch_related('datasetfile_set')
    return render(request, 'dataset_view.html', {'datasets': datasets})

def search_datasets(request):
    query = request.GET.get('q', '')
    subject_area = request.GET.get('subject_area', '')
    associated_task = request.GET.get('associated_task', '')
    feature_type = request.GET.get('feature_type', '')

    filters = {}
    if query:
        filters['title__icontains'] = query
    if subject_area:
        filters['datasetfile__subject_area__icontains'] = subject_area
    if associated_task:
        filters['datasetfile__associated_task__icontains'] = associated_task
    if feature_type:
        filters['datasetfile__feature_type__icontains'] = feature_type

    datasets = Dataset.objects.filter(**filters).prefetch_related('datasetfile_set').distinct()

    results = []
    for dataset in datasets:
        dataset_files = []
        for file in dataset.datasetfile_set.all():
            dataset_files.append({
                'subject_area': file.subject_area,
                'associated_task': file.associated_task,
                'feature_type': file.feature_type,
                'completeness_status': file.completeness_status,
            })
        results.append({
            'id': dataset.id,
            'title': dataset.title,
            'subtitle': dataset.subtitle,
            'profile_graphics': dataset.profile_graphics.url,
            'files': dataset_files,
        })

    return JsonResponse(results, safe=False)

@login_required
def dataset_list_view(request):
    datasets = Dataset.objects.all().prefetch_related('datasetfile_set')
    requests = DatasetRequest.objects.filter(status='pending')
    return render(request, 'dataset_list.html', {'datasets': datasets, 'requests': requests})

def record_dataset_view(dataset):
    today = timezone.now().date()
    dataset_view, created = DatasetView.objects.get_or_create(dataset=dataset, date=today)
    dataset_view.count += 1
    dataset_view.save()

def dataset_detail_view(request, pk):
    dataset = get_object_or_404(Dataset, pk=pk)
    authors = Author.objects.filter(dataset=dataset)
    dataset_files = DatasetFile.objects.filter(dataset=dataset)
    additional_info = AdditionalInfo.objects.filter(dataset=dataset)
    photo_reviews = PhotoReview.objects.filter(dataset=dataset)
    comments = Comment.objects.filter(dataset=dataset).order_by('-created_at')
    views = DatasetView.objects.filter(dataset=dataset).order_by('date')
    comment_form = CommentForm()

    record_dataset_view(dataset)
    
    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.dataset = dataset
            comment.save()
            return JsonResponse({'status': 'success', 'comment': {
                'id': comment.id,
                'text': comment.text,
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }})
        else:
            return JsonResponse({'status': 'error', 'errors': comment_form.errors})

    context = {
        'dataset': dataset,
        'authors': authors,
        'dataset_files': dataset_files,
        'additional_info': additional_info,
        'photo_reviews': photo_reviews,
        'views': views,
        'comments': comments,
        'comment_form': comment_form,
    }
    return render(request, 'dataset_detail.html', context)

def dataset_detail_view_guest(request, pk):
    dataset = get_object_or_404(Dataset, pk=pk)
    authors = Author.objects.filter(dataset=dataset)
    dataset_files = DatasetFile.objects.filter(dataset=dataset)
    additional_info = AdditionalInfo.objects.filter(dataset=dataset)
    photo_reviews = PhotoReview.objects.filter(dataset=dataset)
    comments = Comment.objects.filter(dataset=dataset).order_by('-created_at')
    views = DatasetView.objects.filter(dataset=dataset).order_by('date')
    comment_form = CommentForm()

    record_dataset_view(dataset)
    
    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.dataset = dataset
            comment.save()
            return JsonResponse({'status': 'success', 'comment': {
                'id': comment.id,
                'text': comment.text,
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }})
        else:
            return JsonResponse({'status': 'error', 'errors': comment_form.errors})

    context = {
        'dataset': dataset,
        'authors': authors,
        'dataset_files': dataset_files,
        'additional_info': additional_info,
        'photo_reviews': photo_reviews,
        'views': views,
        'comments': comments,
        'comment_form': comment_form,
    }
    return render(request, 'dataset_detail_guest.html', context)

def delete_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    comment.delete()
    return JsonResponse({'status': 'success'})

def clear_form_session(request):
    for key in ['basic_form', 'author_form', 'dataset_file_form', 'additional_info_form', 'photo_formset']:
        if key in request.session:
            del request.session[key]
    request.session.pop('dataset_id', None)
    return redirect('dataset_list')

def save_form_to_session(request, form, form_name):
    if form.is_valid():
        form_data = form.cleaned_data.copy()
        for key in request.FILES:
            file = request.FILES[key]
            file_name = f"{form_name}_{key}"
            save_file_to_session(request, file, file_name)
            form_data[key] = file_name

        request.session[form_name] = form_data
        return True
    return False

def get_form_from_session(request, form_class, form_name):
    initial = request.session.get(form_name, None)
    return form_class(initial=initial)

def save_profile_image(file):
    img = Image.open(file)
    width, height = img.size
    new_width = min(width, height)
    new_height = new_width
    left = (width - new_width) / 2
    top = (height - new_height) / 2
    right = (width + new_width) / 2
    bottom = (height + new_height) / 2
    img = img.crop((left, top, right, bottom))
    img.save(file.path)

def save_file_to_session(request, file, file_name):
    file_path = f'/tmp/{file_name}'
    with open(file_path, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)
    request.session[file_name] = {
        'path': file_path,
        'original_name': file.name
    }

def get_file_from_session(request, file_name):
    file_info = request.session.get(file_name, None)
    if file_info and isinstance(file_info, dict) and 'path' in file_info:
        file_path = file_info['path']
        original_name = file_info['original_name']
        if os.path.exists(file_path):
            return open(file_path, 'rb'), original_name
    return None, None

def basic_form_view(request):
    dataset_request_id = request.session.pop('dataset_request_id', None)
    if request.method == 'POST':
        form = BasicForm(request.POST, request.FILES)
        if 'next' in request.POST and save_form_to_session(request, form, 'basic_form'):
            dataset = form.save(commit=False)
            if dataset_request_id:
                dataset_request = DatasetRequest.objects.get(id=dataset_request_id)
                dataset.project_name = dataset_request.project_name
                dataset.description_problem = dataset_request.description_problem
                dataset.request_id = dataset_request.id
            if 'profile_graphics' in request.FILES:
                save_file_to_session(request, request.FILES['profile_graphics'], 'profile_graphics')
            dataset.save()
            request.session['dataset_id'] = dataset.id
            logger.debug("Basic form saved, redirecting to author_form")
            return redirect('author_form')
        elif 'back' in request.POST:
            clear_form_session(request)
            return redirect('dataset_list')
    else:
        initial_data = {}
        if dataset_request_id:
            dataset_request = DatasetRequest.objects.get(id=dataset_request_id)
            initial_data = {
                'title': '',
                'subtitle': '',
                'num_instances': '',
                'num_features': '',
                'profile_graphics': '',
                'request_id': dataset_request_id,
                'project_name': dataset_request.project_name,
                'description_problem': dataset_request.description_problem,
            }
            logger.info(f"Initial data for the form: {initial_data}")
        form = get_form_from_session(request, BasicForm, 'basic_form')
        if not form.is_bound:
            form = BasicForm(initial=initial_data)
        if 'profile_graphics' in request.session:
            profile_graphics_file, profile_graphics_name = get_file_from_session(request, 'profile_graphics')
            form.fields['profile_graphics'].initial = profile_graphics_name
    logger.debug("Rendering basic form")
    return render(request, 'basic_form.html', {'form': form})

def author_form_view(request):
    if request.method == 'POST':
        form = AuthorForm(request.POST)
        if 'next' in request.POST:
            logger.debug("Received POST request for 'next'")
            if save_form_to_session(request, form, 'author_form'):
                dataset_id = request.session.get('dataset_id')
                dataset = get_object_or_404(Dataset, id=dataset_id)
                author = form.save(commit=False)
                existing_author = Author.objects.filter(dataset=dataset).first()
                if existing_author:
                    existing_author.verificator = author.verificator
                    existing_author.creator1 = author.creator1
                    existing_author.creator2 = author.creator2
                    existing_author.creator3 = author.creator3
                    existing_author.creator4 = author.creator4
                    existing_author.save()
                else:
                    author.dataset = dataset
                    author.save()
                logger.debug("Author form saved, redirecting to dataset_file_form")
                return redirect('dataset_file_form')
        elif 'back' in request.POST:
            logger.debug("Received POST request for 'back'")
            return redirect('basic_form')
    else:
        form = get_form_from_session(request, AuthorForm, 'author_form')
        logger.debug("Rendering author form")
    return render(request, 'author_form.html', {'form': form})

def dataset_file_form_view(request):
    dataset_id = request.session.get('dataset_id')
    if not dataset_id:
        logger.debug("No dataset_id in session, redirecting to basic_form")
        return redirect('basic_form')

    dataset = Dataset.objects.get(id=dataset_id)

    if request.method == 'POST':
        form = DatasetFileForm(request.POST, request.FILES)

        if 'next' in request.POST and form.is_valid():
            if 'dataset_file' in request.session:
                del request.session['dataset_file']

            dataset_file = DatasetFile.objects.filter(dataset=dataset).first()

            if dataset_file:
                if 'file' in request.FILES:
                    dataset_file.file = request.FILES['file']
                dataset_file.has_missing_values = form.cleaned_data['has_missing_values']
                dataset_file.completeness_status = form.cleaned_data['completeness_status']
                dataset_file.subject_area = form.cleaned_data['subject_area']
                dataset_file.associated_task = form.cleaned_data['associated_task']
                dataset_file.feature_type = form.cleaned_data['feature_type']
                dataset_file.save()
            else:
                dataset_file = form.save(commit=False)
                dataset_file.dataset = dataset
                if 'file' in request.FILES:
                    dataset_file.file = request.FILES['file']
                dataset_file.save()

            save_form_to_session(request, form, 'dataset_file_form')
            logger.debug("Dataset file form saved, redirecting to additional_info_form")
            return redirect('additional_info_form')

        elif 'back' in request.POST:
            logger.debug("Received POST request for 'back'")
            return redirect('author_form')

    else:
        form = get_form_from_session(request, DatasetFileForm, 'dataset_file_form')
        if 'dataset_file' in request.session:
            form.fields['file'].initial, _ = get_file_from_session(request, 'dataset_file')

    return render(request, 'dataset_file_form.html', {'form': form})

def additional_info_form_view(request):
    dataset_id = request.session.get('dataset_id')
    if not dataset_id:
        return redirect('basic_form')
    dataset = Dataset.objects.get(id=dataset_id)
    PhotoReviewFormSet = modelformset_factory(PhotoReview, form=PhotoReviewForm, extra=1)
    
    if request.method == 'POST':
        form = AdditionalInfoForm(request.POST, request.FILES)
        photo_formset = PhotoReviewFormSet(request.POST, request.FILES, queryset=PhotoReview.objects.filter(dataset=dataset))
        
        if 'next' in request.POST and form.is_valid() and photo_formset.is_valid():
            additional_info, created = AdditionalInfo.objects.update_or_create(
                dataset=dataset,
                defaults={
                    'keyword1': form.cleaned_data['keyword1'],
                    'keyword2': form.cleaned_data['keyword2'],
                    'keyword3': form.cleaned_data['keyword3'],
                    'additional_info': form.cleaned_data['additional_info']
                }
            )
            
            for photo_form in photo_formset:
                if photo_form.cleaned_data.get('photo_review'):
                    photo_review = photo_form.save(commit=False)
                    photo_review.dataset = dataset
                    photo_review.save()
                elif 'captured_image' in request.POST and request.POST['captured_image']:
                    image_data = request.POST['captured_image']
                    format, imgstr = image_data.split(';base64,')
                    ext = format.split('/')[-1]
                    photo = ContentFile(base64.b64decode(imgstr), name=f'captured_image.{ext}')
                    photo_review = PhotoReview(dataset=dataset, photo_review=photo)
                    photo_review.save()
            
            save_form_to_session(request, form, 'additional_info_form')
            request.session['photo_formset'] = [photo_form.cleaned_data for photo_form in photo_formset if 'photo_review' not in photo_form.cleaned_data]
            
            return redirect('submission_form')
        elif 'back' in request.POST:
            return redirect('dataset_file_form')
    else:
        form = get_form_from_session(request, AdditionalInfoForm, 'additional_info_form')
        photo_formset = PhotoReviewFormSet(queryset=PhotoReview.objects.filter(dataset=dataset))
        if 'photo_formset' in request.session:
            for i, photo_form in enumerate(photo_formset):
                if f'photo_review_{i}' in request.session:
                    photo_form.fields['photo_review'].initial, _ = get_file_from_session(request, f'photo_review_{i}')
    
    return render(request, 'additional_info_form.html', {'form': form, 'photo_formset': photo_formset})

def submission_form_view(request):
    if request.method == 'POST':
        dataset_id = request.session.get('dataset_id')
        if dataset_id:
            Dataset.objects.filter(id=dataset_id).delete()

        basic_form_data = request.session.pop('basic_form', {})
        author_form_data = request.session.pop('author_form', {})
        dataset_file_form_data = request.session.pop('dataset_file_form', {})
        additional_info_form_data = request.session.pop('additional_info_form', {})
        photo_formset_data = request.session.pop('photo_formset', [])

        dataset = Dataset.objects.create(**basic_form_data)
        Author.objects.create(dataset=dataset, **author_form_data)
        
        dataset_file = DatasetFile.objects.create(dataset=dataset, **{k: v for k, v in dataset_file_form_data.items() if k != 'file'})
        file_info = request.session.get('dataset_file_form_file', None)
        if file_info:
            with open(file_info['path'], 'rb') as file:
                dataset_file.file.save(file_info['original_name'], file, save=True)

        profile_graphics_info = request.session.get('profile_graphics', None)
        if profile_graphics_info:
            with open(profile_graphics_info['path'], 'rb') as file:
                dataset.profile_graphics.save(profile_graphics_info['original_name'], file, save=True)

        additional_info_cleaned_data = {key: value for key, value in additional_info_form_data.items() if key in AdditionalInfoForm.Meta.fields}
        AdditionalInfo.objects.create(dataset=dataset, **additional_info_cleaned_data)
        
        for i, photo_data in enumerate(photo_formset_data):
            if 'photo_review' in photo_data:
                file_name = f'photo_review_{i}'
                file_info = request.session.get(file_name, None)
                if file_info:
                    with open(file_info['path'], 'rb') as file:
                        photo_review = PhotoReview(dataset=dataset)
                        photo_review.photo_review.save(file_info['original_name'], file, save=True)
                        photo_review.save()

        clear_form_session(request)
        save_dataset_and_update_status(dataset)
        return redirect('dataset_list')

    dataset_id = request.session.get('dataset_id')
    if not dataset_id:
        return redirect('basic_form')

    dataset = Dataset.objects.get(id=dataset_id)
    authors = Author.objects.filter(dataset=dataset)
    dataset_files = DatasetFile.objects.filter(dataset=dataset)
    additional_info = AdditionalInfo.objects.filter(dataset=dataset)
    photo_reviews = PhotoReview.objects.filter(dataset=dataset)

    return render(request, 'submission_form.html', {
        'dataset': dataset,
        'authors': authors,
        'dataset_files': dataset_files,
        'additional_info': additional_info,
        'photo_reviews': photo_reviews,
    })

def delete_dataset_view(request, dataset_id):
    dataset = get_object_or_404(Dataset, id=dataset_id)
    dataset.delete()
    return redirect('dataset_list')

def edit_dataset_view(request, dataset_id):
    dataset = get_object_or_404(Dataset, id=dataset_id)

    if request.method == 'POST':
        dataset_form = BasicForm(request.POST, request.FILES, instance=dataset)
        author_form = AuthorForm(request.POST, instance=Author.objects.filter(dataset=dataset).first())
        dataset_file_form = DatasetFileForm(request.POST, request.FILES, instance=DatasetFile.objects.filter(dataset=dataset).first())
        additional_info_form = AdditionalInfoForm(request.POST, request.FILES, instance=AdditionalInfo.objects.filter(dataset=dataset).first())
        photo_review_form = PhotoReviewForm(request.POST, request.FILES, instance=PhotoReview.objects.filter(dataset=dataset).first())

        if dataset_form.is_valid() and author_form.is_valid() and dataset_file_form.is_valid() and additional_info_form.is_valid() and photo_review_form.is_valid():
            dataset = dataset_form.save(commit=False)
            dataset.updated_at = timezone.now()
            dataset.save()

            author = author_form.save(commit=False)
            author.dataset = dataset
            author.save()

            dataset_file = dataset_file_form.save(commit=False)
            dataset_file.dataset = dataset
            dataset_file.save()

            additional_info = additional_info_form.save(commit=False)
            additional_info.dataset = dataset
            additional_info.save()

            photo_review = photo_review_form.save(commit=False)
            photo_review.dataset = dataset
            photo_review.save()

            send_status_to_endpoint(dataset)
            return redirect('dataset_list')
    else:
        dataset_form = BasicForm(instance=dataset)
        author_form = AuthorForm(instance=Author.objects.filter(dataset=dataset).first())
        dataset_file_form = DatasetFileForm(instance=DatasetFile.objects.filter(dataset=dataset).first())
        additional_info_form = AdditionalInfoForm(instance=AdditionalInfo.objects.filter(dataset=dataset).first())
        photo_review_form = PhotoReviewForm(instance=PhotoReview.objects.filter(dataset=dataset).first())

    return render(request, 'edit_dataset.html', {
        'dataset_form': dataset_form,
        'author_form': author_form,
        'dataset_file_form': dataset_file_form,
        'additional_info_form': additional_info_form,
        'photo_review_form': photo_review_form,
    })

def create_dataset_view(request):
    pending_requests = DatasetRequest.objects.filter(status='pending')
    if pending_requests.exists():
        return redirect('dataset_requests')
    return redirect('basic_form')

def dataset_requests_view(request):
    requests = DatasetRequest.objects.filter(status='pending')
    return render(request, 'dataset_list.html', {'requests': requests})

def check_dataset_requests(request):
    has_requests = DatasetRequest.objects.filter(status='pending').exists()
    return JsonResponse({'has_requests': has_requests})

IC_API_URL = 'https://testapp.requestcatcher.com/test'

@csrf_exempt
@api_view(['POST'])
def update_request_status(request):
    if request.method == 'POST':
        data = request.data
        request_id = data.get('request_id')
        status = data.get('status')

        try:
            dataset_request = DatasetRequest.objects.get(id=request_id)
            dataset_request.status = status
            dataset_request.save()
            return JsonResponse({'status': 'success'})
        except DatasetRequest.DoesNotExist:
            return JsonResponse({'status': 'failed', 'error': 'Request not found'}, status=404)

    return JsonResponse({'status': 'failed', 'error': 'Invalid method'}, status=400)

def accept_request(request, request_id):
    dataset_request = get_object_or_404(DatasetRequest, id=request_id)
    request.session['dataset_request_id'] = dataset_request.id
    dataset_request.status = 'accepted'
    dataset_request.save()
    try:
        response = requests.post(IC_API_URL, json={'request_id': request_id, 'status': 'accepted'})
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to connect to IC API: {e}")
    return redirect('basic_form')

def ignore_request(request, request_id):
    dataset_request = get_object_or_404(DatasetRequest, id=request_id)
    dataset_request.status = 'ignored'
    dataset_request.save()
    try:
        response = requests.post(IC_API_URL, json={'request_id': request_id, 'status': 'ignored'})
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to connect to IC API: {e}")
    return redirect('dataset_list')

def save_dataset_and_update_status(dataset):
    dataset.save()
    try:
        dataset_file = DatasetFile.objects.filter(dataset=dataset).first()
        if dataset_file.completeness_status == 'Complete':
            file_data = open(dataset_file.file.path, 'rb').read()
            response = requests.post(IC_API_URL, json={'request_id': dataset.request_id, 'status': dataset_file.completeness_status, 'file': dataset_file.file.name})
            response.raise_for_status()
            files = {'file': (dataset_file.file.name, file_data)}
            response = requests.post(IC_API_URL, files=files)
            response.raise_for_status()
        else:
            response = requests.post(IC_API_URL, json={'request_id': dataset.request_id, 'status': dataset_file.completeness_status})
            response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to connect to IC API: {e}")

def send_status_to_endpoint(dataset):
    IC_API_URL = 'https://testapp.requestcatcher.com/test'
    try:
        dataset_file = DatasetFile.objects.filter(dataset=dataset).first()
        completeness_status = dataset_file.completeness_status if dataset_file else 'Unknown'

        data = {
            'request_id': dataset.request_id,
            'status': completeness_status
        }

        if completeness_status == 'Complete' and dataset_file:
            file_path = dataset_file.file.path
            with open(file_path, 'rb') as file:
                files = {'file': (dataset_file.file.name, file, 'application/octet-stream')}
                response = requests.post(IC_API_URL, data=data, files=files)
        else:
            response = requests.post(IC_API_URL, json=data)

        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send status to endpoint: {e}")

class DatasetRequestAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DatasetRequestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


