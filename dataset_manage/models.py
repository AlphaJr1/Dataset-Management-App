from django.db import models
from django.utils import timezone

class Dataset(models.Model):
    title = models.CharField(max_length=255, default='', verbose_name="Dataset Title")
    subtitle = models.TextField(default='', verbose_name="Subtitle")
    num_instances = models.IntegerField(verbose_name="Number of Instances")
    num_features = models.IntegerField(verbose_name="Number of Features")
    profile_graphics = models.ImageField(upload_to='profile_graphics/', default='default_image.jpg', verbose_name="Profile Graphics")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Dataset"
        verbose_name_plural = "Datasets"

class DatasetView(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='views')
    date = models.DateField(default=timezone.now)
    count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('dataset', 'date')

class Author(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='authors')
    verificator = models.CharField(max_length=255)
    creator1 = models.CharField(max_length=255)
    creator2 = models.CharField(max_length=255, null=True, blank=True)
    creator3 = models.CharField(max_length=255, null=True, blank=True)
    creator4 = models.CharField(max_length=255, null=True, blank=True)

COMPLETENESS_STATUS_CHOICES = [
    ('Complete', 'Complete'),
    ('Ongoing', 'Ongoing'),
    ('Failed', 'Failed')
]

SUBJECT_AREA_CHOICES = [
    ('Computer Vision', 'Computer Vision'),
    ('Natural Language Processing', 'Natural Language Processing'),
    ('Speech Recognition', 'Speech Recognition'),
    ('Healthcare', 'Healthcare'),
    ('Finance', 'Finance'),
    ('Marketing', 'Marketing'),
    ('Autonomous Systems', 'Autonomous Systems'),
    ('Agriculture', 'Agriculture'),
    ('Energy', 'Energy'),
    ('Other', 'Other...')
]

ASSOCIATED_TASK_CHOICES = [
    ('Classification', 'Classification'),
    ('Regression', 'Regression'),
    ('Clustering', 'Clustering'),
    ('Recommendation', 'Recommendation'),
    ('Anomaly Detection', 'Anomaly Detection'),
    ('Dimensionality Reduction', 'Dimensionality Reduction'),
    ('Time Series Forecasting', 'Time Series Forecasting'),
    ('Reinforcement Learning', 'Reinforcement Learning'),
    ('Other', 'Other...')
]

FEATURE_TYPE_CHOICES = [
    ('Numerical', 'Numerical'),
    ('Categorical', 'Categorical'),
    ('Text', 'Text'),
    ('Image', 'Image'),
    ('Audio', 'Audio'),
    ('Temporal', 'Temporal'),
    ('Geospatial', 'Geospatial'),
    ('Binary', 'Binary'),
    ('Composite', 'Composite'),
    ('Other', 'Other...')
]

class DatasetFile(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    file = models.FileField(upload_to='dataset_files/')
    has_missing_values = models.BooleanField(default=False)
    completeness_status = models.CharField(max_length=50, choices=COMPLETENESS_STATUS_CHOICES)
    subject_area = models.CharField(max_length=100, choices=SUBJECT_AREA_CHOICES, null=True, blank=True)
    associated_task = models.CharField(max_length=100, choices=ASSOCIATED_TASK_CHOICES, null=True, blank=True)
    feature_type = models.CharField(max_length=100, choices=FEATURE_TYPE_CHOICES, null=True, blank=True)

class AdditionalInfo(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    keyword1 = models.CharField(max_length=100, null=True, blank=True)
    keyword2 = models.CharField(max_length=100, null=True, blank=True)
    keyword3 = models.CharField(max_length=100, null=True, blank=True)
    additional_info = models.TextField(null=True, blank=True)

class PhotoReview(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    photo_review = models.ImageField(upload_to='photo_reviews/')

class Comment(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.text[:50]
