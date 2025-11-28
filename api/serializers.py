from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.conf import settings

from .models import Document

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2')
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')

class DocumentSerializer(serializers.ModelSerializer):
    file = serializers.FileField()
    class Meta:
        model = Document
        fields = ('id', 'title', 'file', 'uploaded_at', 'processed')
        read_only_fields = ('uploaded_at', 'processed')
        
    def get_file(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.file.url)

class DocumentUploadSerializer(serializers.ModelSerializer):
    file = serializers.FileField()

    class Meta:
        model = Document
        fields = ('file',)

    def validate_file(self, value):
        if not value.name.endswith('.pdf'):
            raise serializers.ValidationError("Only PDF files are allowed.")
        
        # Check file size
        if value.size >= settings.MAX_UPLOAD_SIZE:
            raise serializers.ValidationError(f"File size must be less than or equal to {settings.MAX_UPLOAD_SIZE / (1024 * 1024):.0f}MB.")
        
        return value
