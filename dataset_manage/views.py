from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.forms import modelformset_factory
from .forms import BasicForm, AuthorForm, DatasetFileForm, AdditionalInfoForm, PhotoReviewForm, CommentForm
from .models import Dataset, Author, DatasetFile, AdditionalInfo, PhotoReview, DatasetView, Comment
from PIL import Image
import logging
from django.core.files.base import ContentFile
import base64
import os
from django.http import JsonResponse
from django.utils import timezone


logger = logging.getLogger(__name__)

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

def save_file_to_session(request, file, file_name):
    file_path = f'/tmp/{file_name}'
    with open(file_path, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)
    request.session[file_name] = file_path

def get_file_from_session(request, file_name):
    file_path = request.session.get(file_name, None)
    if file_path and os.path.exists(file_path):
        return open(file_path, 'rb')
    return None

def dataset_list_view(request):
    datasets = Dataset.objects.all().prefetch_related('datasetfile_set')
    return render(request, 'dataset_list.html', {'datasets': datasets})

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
            if key in form_data:
                del form_data[key]
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

def basic_form_view(request):
    if request.method == 'POST':
        form = BasicForm(request.POST, request.FILES)
        if 'next' in request.POST and save_form_to_session(request, form, 'basic_form'):
            dataset = form.save(commit=False)
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
        form = get_form_from_session(request, BasicForm, 'basic_form')
        if 'profile_graphics' in request.session:
            form.fields['profile_graphics'].initial = get_file_from_session(request, 'profile_graphics')
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
                    # Update existing author
                    existing_author.verificator = author.verificator
                    existing_author.creator1 = author.creator1
                    existing_author.creator2 = author.creator2
                    existing_author.creator3 = author.creator3
                    existing_author.creator4 = author.creator4
                    existing_author.save()
                else:
                    # Save new author
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
            dataset_file = DatasetFile.objects.filter(dataset=dataset).first()
            if dataset_file:
                # Update existing DatasetFile
                dataset_file.file = form.cleaned_data['file']
                dataset_file.has_missing_values = form.cleaned_data['has_missing_values']
                dataset_file.completeness_status = form.cleaned_data['completeness_status']
                dataset_file.subject_area = form.cleaned_data['subject_area']
                dataset_file.associated_task = form.cleaned_data['associated_task']
                dataset_file.feature_type = form.cleaned_data['feature_type']
                dataset_file.save()
            else:
                # Create new DatasetFile
                dataset_file = form.save(commit=False)
                dataset_file.dataset = dataset
                if 'file' in request.FILES:
                    save_file_to_session(request, request.FILES['file'], 'dataset_file')
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
            form.fields['file'].initial = get_file_from_session(request, 'dataset_file')
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

            for i, photo_form in enumerate(photo_formset):
                if photo_form.cleaned_data.get('photo_review'):
                    photo_review = photo_form.save(commit=False)
                    photo_review.dataset = dataset
                    photo_review.save()
                    save_file_to_session(request, photo_form.cleaned_data['photo_review'], f'photo_review_{i}')
                elif f'captured_image_{i}' in request.POST and request.POST[f'captured_image_{i}']:
                    image_data = request.POST[f'captured_image_{i}']
                    format, imgstr = image_data.split(';base64,')
                    ext = format.split('/')[-1]
                    photo = ContentFile(base64.b64decode(imgstr), name=f'captured_image_{i}.{ext}')
                    photo_review = PhotoReview(dataset=dataset, photo_review=photo)
                    photo_review.save()
                    save_file_to_session(request, photo, f'captured_image_{i}')

            save_form_to_session(request, form, 'additional_info_form')
            request.session['photo_formset'] = [photo_form.cleaned_data for photo_form in photo_formset if 'photo_review' not in photo_form.cleaned_data]

            return redirect('submission_form')
        elif 'back' in request.POST:
            return redirect('dataset_file_form')
    else:
        form = get_form_from_session(request, AdditionalInfoForm, 'additional_info_form')
        photo_formset = PhotoReviewFormSet(queryset=PhotoReview.objects.filter(dataset=dataset))
        if 'photo_formset' in request.session:
            for photo_form in photo_formset:
                if f'photo_review_{photo_form.prefix}' in request.session:
                    photo_form.fields['photo_review'].initial = get_file_from_session(request, f'photo_review_{photo_form.prefix}')
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
        dataset_file = DatasetFile.objects.create(dataset=dataset, **dataset_file_form_data)

        # Save the file from session to the newly created DatasetFile object
        file_path = request.session.get('dataset_file', None)
        if file_path:
            with open(file_path, 'rb') as file:
                dataset_file.file.save(os.path.basename(file_path), file, save=True)

        # Save profile_graphics
        profile_graphics_path = request.session.get('profile_graphics', None)
        if profile_graphics_path:
            with open(profile_graphics_path, 'rb') as file:
                dataset.profile_graphics.save(os.path.basename(profile_graphics_path), file, save=True)

        AdditionalInfo.objects.create(dataset=dataset, **additional_info_form_data)
        for i, photo_data in enumerate(photo_formset_data):
            if 'photo_review' in photo_data:
                file_name = f'photo_review_{i}'
                file_path = request.session.get(file_name, None)
                if file_path:
                    with open(file_path, 'rb') as file:
                        photo_review = PhotoReview(dataset=dataset)
                        photo_review.photo_review.save(os.path.basename(file_path), file, save=True)
                        photo_review.save()

        clear_form_session(request)
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
    AuthorFormSet = modelformset_factory(Author, form=AuthorForm, extra=0)
    DatasetFileFormSet = modelformset_factory(DatasetFile, form=DatasetFileForm, extra=0)
    AdditionalInfoFormSet = modelformset_factory(AdditionalInfo, form=AdditionalInfoForm, extra=0)
    PhotoReviewFormSet = modelformset_factory(PhotoReview, form=PhotoReviewForm, extra=1)

    if request.method == 'POST':
        dataset_form = BasicForm(request.POST, request.FILES, instance=dataset)
        author_formset = AuthorFormSet(request.POST, queryset=Author.objects.filter(dataset=dataset))
        dataset_file_formset = DatasetFileFormSet(request.POST, request.FILES, queryset=DatasetFile.objects.filter(dataset=dataset))
        additional_info_formset = AdditionalInfoFormSet(request.POST, request.FILES, queryset=AdditionalInfo.objects.filter(dataset=dataset))
        photo_formset = PhotoReviewFormSet(request.POST, request.FILES, queryset=PhotoReview.objects.filter(dataset=dataset))

        if dataset_form.is_valid() and author_formset.is_valid() and dataset_file_formset.is_valid() and additional_info_formset.is_valid() and photo_formset.is_valid():
            dataset = dataset_form.save()
            for form in author_formset:
                author = form.save(commit=False)
                existing_author = Author.objects.filter(dataset=dataset).first()
                if existing_author:
                    # Update existing author
                    existing_author.verificator = author.verificator
                    existing_author.creator1 = author.creator1
                    existing_author.creator2 = author.creator2
                    existing_author.creator3 = author.creator3
                    existing_author.creator4 = author.creator4
                    existing_author.save()
                else:
                    # Save new author
                    author.dataset = dataset
                    author.save()

            for form in dataset_file_formset:
                dataset_file = form.save(commit=False)
                existing_file = DatasetFile.objects.filter(dataset=dataset).first()
                if existing_file:
                    existing_file.file = dataset_file.file
                    existing_file.has_missing_values = dataset_file.has_missing_values
                    existing_file.completeness_status = dataset_file.completeness_status
                    existing_file.subject_area = dataset_file.subject_area
                    existing_file.associated_task = dataset_file.associated_task
                    existing_file.feature_type = dataset_file.feature_type
                    existing_file.save()
                else:
                    dataset_file.dataset = dataset
                    dataset_file.save()

            for form in additional_info_formset:
                additional_info = form.save(commit=False)
                existing_info = AdditionalInfo.objects.filter(dataset=dataset).first()
                if existing_info:
                    existing_info.keyword1 = additional_info.keyword1
                    existing_info.keyword2 = additional_info.keyword2
                    existing_info.keyword3 = additional_info.keyword3
                    existing_info.additional_info = additional_info.additional_info
                    existing_info.save()
                else:
                    additional_info.dataset = dataset
                    additional_info.save()

            for form in photo_formset:
                if form.cleaned_data.get('photo_review'):
                    photo_review = form.save(commit=False)
                    existing_photo = PhotoReview.objects.filter(dataset=dataset).first()
                    if existing_photo:
                        existing_photo.photo_review = photo_review.photo_review
                        existing_photo.save()
                    else:
                        photo_review.dataset = dataset
                        photo_review.save()

            return redirect('dataset_list')
    else:
        dataset_form = BasicForm(instance=dataset)
        author_formset = AuthorFormSet(queryset=Author.objects.filter(dataset=dataset))
        dataset_file_formset = DatasetFileFormSet(queryset=DatasetFile.objects.filter(dataset=dataset))
        additional_info_formset = AdditionalInfoFormSet(queryset=AdditionalInfo.objects.filter(dataset=dataset))
        photo_formset = PhotoReviewFormSet(queryset=PhotoReview.objects.filter(dataset=dataset))

    return render(request, 'edit_dataset.html', {
        'dataset_form': dataset_form,
        'author_formset': author_formset,
        'dataset_file_formset': dataset_file_formset,
        'additional_info_formset': additional_info_formset,
        'photo_formset': photo_formset,
    })




