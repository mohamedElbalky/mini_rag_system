from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
import logging

from utils.helpers import create_response

from .serializers import UserRegistrationSerializer, UserSerializer, DocumentSerializer, DocumentUploadSerializer
from .models import Document
from .utils.pdf_processor import PDFProcessor
from .utils.vector_store import VectorStoreManager

logger = logging.getLogger(__name__)

# Authentication Views
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Register a new user
    """
    try:
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)

            return create_response(
                success=True,
                message='User registered successfully',
                data={
                    'user': UserSerializer(user).data,
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    }
                },
                status_code=status.HTTP_201_CREATED
            )
        
        return create_response(
            success=False,
            message='Registration failed',
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception as e:
        logger.error(f"An error occurred during registration: {str(e)}")
        return create_response(
            success=False,
            message='An error occurred during registration',
            errors=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Login user and return JWT tokens
    """
    try:
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return create_response(
                success=False,
                message='Username and password are required',
                status_code=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(username=username, password=password)

        if user is not None:
            refresh = RefreshToken.for_user(user)
            
            return create_response(
                success=True,
                message='Login successful',
                data={
                    'user': UserSerializer(user).data,
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    }
                },
                status_code=status.HTTP_200_OK
            )
        
        return create_response(
            success=False,
            message='Invalid credentials',
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    except Exception as e:
        logger.error(f"An error occurred during login: {str(e)}")
        return create_response(
            success=False,
            message='An error occurred during login',
            errors=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ---- Document Views ----
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_documents(request):
    """
    List all documents for the authenticated user
    """
    try:
        documents = Document.objects.filter(user=request.user)
        serializer = DocumentSerializer(documents, many=True)
        
        return create_response(
            success=True,
            message='Documents retrieved successfully',
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
    
    except Exception as e:
        logger.error(f"Failed to retrieve documents: {str(e)}")
        return create_response(
            success=False,
            message='Failed to retrieve documents',
            errors=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_document(request, document_id):
    """
    Delete a document
    """
    try:
        document = Document.objects.get(id=document_id, user=request.user)
        document.delete()
        
        logger.info(f"Document deleted: ID {document_id} for user {request.user}")
        return create_response(
            success=True,
            message='Document deleted successfully',
            status_code=status.HTTP_200_OK
        )
    
    except Document.DoesNotExist:
        logger.error(f"Document not found: ID {document_id} for user {request.user}")
        return create_response(
            success=False,
            message='Document not found',
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    except Exception as e:
        logger.error(f"Failed to delete document: {str(e)}")
        return create_response(
            success=False,
            message='Failed to delete document',
            errors=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_document(request):
    """
    Upload a document

    This endpoint accepts a file upload and processes the uploaded
    PDF to extract text and create a vector store.

    The response will contain the processed document data.

    :param request: Request object
    :return: Response object
    :raises: Exception
    """
    try:
        if 'file' not in request.FILES:
            return create_response(
                success=False,
                message='No file provided',
                status_code=status.HTTP_400_BAD_REQUEST
            )

        serializer = DocumentUploadSerializer(data=request.data)
        
        if not serializer.is_valid():
            return create_response(
                success=False,
                message='Invalid file upload',
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        file = request.FILES['file']
        
        # Create document record
        document = Document.objects.create(
            user=request.user,
            title=file.name,
            file=file
        )

        # Process PDF
        try:
            # Extract text from PDF
            pdf_processor = PDFProcessor()
            text_chunks = pdf_processor.process_pdf(document.file.path)
            
            if not text_chunks:
                document.delete()
                return create_response(
                    success=False,
                    message='Failed to extract text from PDF',
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Create vector store
            vector_store_manager = VectorStoreManager()
            vector_store_path = vector_store_manager.create_vector_store(
                text_chunks,
                document.id
            )

            # Update document
            document.processed = True
            document.vector_store_path = vector_store_path
            document.text_chunks_count = len(text_chunks)
            document.save()

            return create_response(
                success=True,
                message='Document uploaded and processed successfully',
                data=DocumentSerializer(document).data,
                status_code=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            logger.error(f"Failed to process document {document.id} for user {request.user}: {str(e)}")
            document.delete()
            return create_response(
                success=False,
                message='Failed to process document',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    except Exception as e:
        logger.error(f"An error occurred during document upload: {str(e)}")
        return create_response(
            success=False,
            message='An error occurred during document upload',
            errors=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
