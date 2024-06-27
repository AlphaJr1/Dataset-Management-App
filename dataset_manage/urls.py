from django.urls import path
from .views import (
    basic_form_view, author_form_view, dataset_file_form_view,
    additional_info_form_view, submission_form_view,
    dataset_list_view, delete_dataset_view, edit_dataset_view, 
    clear_form_session, dataset_detail_view, search_datasets,
    delete_comment
)
from .api_views import DatasetInfoAPIView

urlpatterns = [
    path('', dataset_list_view, name='dataset_list'),
    path('dataset/<int:pk>/', dataset_detail_view, name='dataset_detail'),
    path('basic/', basic_form_view, name='basic_form'),
    path('author/', author_form_view, name='author_form'),
    path('dataset_file/', dataset_file_form_view, name='dataset_file_form'),
    path('additional/', additional_info_form_view, name='additional_info_form'),
    path('submission/', submission_form_view, name='submission_form'),
    path('datasets/', dataset_list_view, name='dataset_list'),
    path('datasets/delete/<int:dataset_id>/', delete_dataset_view, name='dataset_delete'),
    path('datasets/edit/<int:dataset_id>/', edit_dataset_view, name='dataset_edit'),
    path('clear_session/', clear_form_session, name='clear_form_session'),
    path('api/datasetinfo/', DatasetInfoAPIView.as_view(), name='dataset_info'),
    path('search/', search_datasets, name='search_datasets'),
    path('comment/delete/<int:pk>/', delete_comment, name='delete_comment')
]
