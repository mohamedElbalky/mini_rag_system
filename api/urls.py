from django.urls import path
from .views import register, login, list_documents, delete_document, upload_document

urlpatterns = [
    # Authentication
    path('auth/register/', register, name='register'),
    path('auth/login/', login, name='login'),
    
    # Document management
    path('documents/', list_documents, name='list_documents'),
    path('documents/delete/<int:document_id>/', delete_document, name='delete_document'),
    path('documents/upload/', upload_document, name='upload_document'),
]