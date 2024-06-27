from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .models import Dataset
from .serializers import DatasetSerializer

class DatasetInfoAPIView(APIView):

    def get(self, request, *args, **kwargs):
        try:
            dataset = Dataset.objects.first()
            if not dataset:
                return Response({"detail": "Dataset not found."}, status=status.HTTP_404_NOT_FOUND)
            serializer = DatasetSerializer(dataset)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Dataset.DoesNotExist:
            return Response({"detail": "Dataset not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, *args, **kwargs):
        serializer = DatasetSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
