from rest_framework import serializers
from .models import Dataset, Author, DatasetFile, AdditionalInfo, PhotoReview, DatasetRequest

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['verificator', 'creator1', 'creator2', 'creator3', 'creator4']

class DatasetFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatasetFile
        fields = ['file', 'has_missing_values', 'completeness_status', 'subject_area', 'associated_task', 'feature_type']

class AdditionalInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdditionalInfo
        fields = ['keyword1', 'keyword2', 'keyword3', 'additional_info']

class PhotoReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhotoReview
        fields = ['photo_review']

class DatasetSerializer(serializers.ModelSerializer):
    authors = AuthorSerializer(many=True, read_only=True)
    dataset_files = DatasetFileSerializer(many=True, read_only=True)
    additional_infos = AdditionalInfoSerializer(many=True, read_only=True)
    photo_reviews = PhotoReviewSerializer(many=True, read_only=True)

    class Meta:
        model = Dataset
        fields = ['title', 'subtitle', 'num_instances', 'num_features', 'profile_graphics', 'authors', 'dataset_files', 'additional_infos', 'photo_reviews']

class DatasetRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatasetRequest
        fields = ['project_name', 'description_problem', 'description_target', 'start_date', 'end_date', 'notes', 'status', 'completeness_status']