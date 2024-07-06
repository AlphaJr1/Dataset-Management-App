from django.urls import path
from .views import (
    basic_form_view, author_form_view, dataset_file_form_view,
    additional_info_form_view, submission_form_view,
    dataset_list_view, delete_dataset_view, edit_dataset_view, 
    clear_form_session, dataset_detail_view, search_datasets,
    delete_comment, create_dataset_view, dataset_requests_view,
    accept_request, ignore_request, check_dataset_requests,
    update_request_status, landing_page_view, dataset_view,
    dataset_detail_view_guest, CustomLoginView, custom_logout_view,
)
from .api_views import DatasetInfoAPIView, DatasetRequestAPI


urlpatterns = [
    path('', landing_page_view, name='landing_page'),
    path('dataset_view/', dataset_view, name='dataset_view'),
    path('dataset/', dataset_list_view, name='dataset_list'),
    path('datasets/<int:pk>/', dataset_detail_view_guest, name='dataset_detail_guest'),
    path('dataset/<int:pk>/', dataset_detail_view, name='dataset_detail'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', custom_logout_view, name='logout'),
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
    path('comment/delete/<int:pk>/', delete_comment, name='delete_comment'),
    path('create_dataset/', create_dataset_view, name='create_dataset'),
    path('dataset_requests/', dataset_requests_view, name='dataset_requests'),
    path('dataset_requests/accept/<int:request_id>/', accept_request, name='accept_request'),
    path('dataset_requests/ignore/<int:request_id>/', ignore_request, name='ignore_request'),
    path('check_dataset_requests/', check_dataset_requests, name='check_dataset_requests'),
    path('api/update_request_status/', update_request_status, name='update_request_status'),
    path('api/dataset_requests/', DatasetRequestAPI.as_view(), name='dataset_requests_api'),
]
