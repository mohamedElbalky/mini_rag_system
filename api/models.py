import os

from django.db import models
from django.contrib.auth.models import User

class Document(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    vector_store_path = models.CharField(max_length=500, blank=True, null=True)
    text_chunks_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.title} - {self.user.username}"

    def delete(self, *args, **kwargs):
        # Delete file when document is deleted
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        
        # Delete vector store files
        if self.vector_store_path and os.path.exists(self.vector_store_path):
            import shutil
            shutil.rmtree(os.path.dirname(self.vector_store_path))
        
        super().delete(*args, **kwargs)