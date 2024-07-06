from django import forms
from django.forms import modelformset_factory
from .models import Dataset, Author, DatasetFile, AdditionalInfo, PhotoReview, Comment

class BasicForm(forms.ModelForm):
    class Meta:
        model = Dataset
        fields = ['title', 'subtitle', 'num_instances', 'num_features', 'profile_graphics', 'project_name', 'description_problem', 'request_id']
        labels = {
            'title': 'Dataset Title',
            'subtitle': 'Subtitle',
            'num_instances': 'Number of Instances (Rows) in Dataset',
            'num_features': 'Number of Features in Dataset',
            'profile_graphics': 'Profile Graphics',
            'project_name':'Project Name',
            'description_problem': 'Description Problem',
            'request_id': 'Request ID',
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'crispy-input', 'placeholder': 'Enter Dataset Title'}),
            'subtitle': forms.TextInput(attrs={'class': 'crispy-input', 'placeholder': 'Enter Subtitle'}),
            'num_instances': forms.NumberInput(attrs={'class': 'crispy-input', 'placeholder': 'Enter Number of Instances'}),
            'num_features': forms.NumberInput(attrs={'class': 'crispy-input', 'placeholder': 'Enter Number of Features'}),
            'profile_graphics': forms.ClearableFileInput(attrs={'class': 'custom-file-upload', 'placeholder': 'Choose a file or drag and drop here'}),
            'project_name': forms.TextInput(attrs={'readonly': 'readonly', 'class': 'crispy-input'}),
            'description_problem': forms.TextInput(attrs={'readonly': 'readonly', 'class': 'crispy-input'}),
            'request_id': forms.TextInput(attrs={'readonly': 'readonly', 'class': 'crispy-input'}),
        }
    def __init__(self, *args, **kwargs):
        super(BasicForm, self).__init__(*args, **kwargs)
        if not self.initial.get('project_name'):
            self.fields['project_name'].widget = forms.HiddenInput()
        if not self.initial.get('description_problem'):
            self.fields['description_problem'].widget = forms.HiddenInput()

class AuthorForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = ['verificator', 'creator1', 'creator2', 'creator3', 'creator4']
        labels = {
            'verificator': 'Add Verificator', 
            'creator1': 'Add Creators', 
            'creator2': '', 
            'creator3': '', 
            'creator4': '',
        }
        widgets = {
            'verificator': forms.TextInput(attrs={'class': 'crispy-input', 'placeholder': 'Enter Verificator Name'}),
            'creator1': forms.TextInput(attrs={'class': 'crispy-input', 'placeholder': 'Enter Creator Name'}),
            'creator2': forms.TextInput(attrs={'class': 'crispy-input', 'placeholder': 'Enter Creator Name'}),
            'creator3': forms.TextInput(attrs={'class': 'crispy-input', 'placeholder': 'Enter Creator Name'}),
            'creator4': forms.TextInput(attrs={'class': 'crispy-input', 'placeholder': 'Enter Creator Name'}),
        }

class DatasetFileForm(forms.ModelForm):
    class Meta:
        model = DatasetFile
        fields = ['file', 'has_missing_values', 'completeness_status', 'subject_area', 'associated_task', 'feature_type']
        labels = {
            'file': 'Dataset Files', 
            'has_missing_values': 'Does data have missing value?',
            'completeness_status': 'What is the completeness status of your dataset?',
            'subject_area': 'What is the subject area of your dataset?', 
            'associated_task': 'What is the associated task for your dataset?',
            'feature_type': 'What is the feature type in your dataset?',
        }
        widgets = {
            'file': forms.ClearableFileInput(attrs={'class': 'custom-file-upload', 'placeholder': 'Choose a file or drag and drop here'}),
            'has_missing_values': forms.CheckboxInput(attrs={'class': 'custom-checkbox'}),
            'completeness_status': forms.Select(attrs={'class': 'crispy-input'}),
            'subject_area': forms.Select(attrs={'class': 'crispy-input'}),
            'associated_task': forms.Select(attrs={'class': 'crispy-input'}),
            'feature_type': forms.Select(attrs={'class': 'crispy-input'}),
        }

class AdditionalInfoForm(forms.ModelForm):
    class Meta:
        model = AdditionalInfo
        fields = ['keyword1', 'keyword2', 'keyword3', 'additional_info']
        labels = {
            'keyword1': 'Add your dataset keyword', 
            'keyword2': '',
            'keyword3': '',
            'additional_info': 'Additional information',
        }
        widgets = {
            'keyword1': forms.TextInput(attrs={'class': 'crispy-input', 'placeholder': ''}),
            'keyword2': forms.TextInput(attrs={'class': 'crispy-input'}),
            'keyword3': forms.TextInput(attrs={'class': 'crispy-input'}),
            'additional_info': forms.Textarea(attrs={'class': 'crispy-input'}),
        }

class PhotoReviewForm(forms.ModelForm):
    class Meta:
        model = PhotoReview
        fields = ['photo_review']
        labels = {
            'photo_review': 'Add dataset photo review',
        }
        widgets = {
            'photo_review': forms.ClearableFileInput(attrs={'class': 'custom-file-upload', 'placeholder': 'Choose a file or drag and drop here'}),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        labels = {
            'text': ''
        }
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'comment-text',
                'placeholder': 'Add your reviews...'}),
        }
        

# Formsets for managing multiple forms
#AuthorFormSet = modelformset_factory(Author, form=AuthorForm, extra=0)
#DatasetFileFormSet = modelformset_factory(DatasetFile, form=DatasetFileForm, extra=0)
#AdditionalInfoFormSet = modelformset_factory(AdditionalInfo, form=AdditionalInfoForm, extra=0)
#PhotoReviewFormSet = forms.modelformset_factory(PhotoReview, form=PhotoReviewForm, extra=1)

