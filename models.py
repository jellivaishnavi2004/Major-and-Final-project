from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
import json
import numpy as np

class UploadedFile(models.Model):
    FILE_CATEGORIES = [
        ('files', 'Documents & Files'),
        ('videos', 'Videos & Movies'),
        ('audio', 'Music & Audio'),
        ('general', 'General Files'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_files')
    original_name = models.CharField(max_length=255)
    saved_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    file_size = models.BigIntegerField()
    category = models.CharField(max_length=20, choices=FILE_CATEGORIES, default='general')
    uploaded_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'uploaded_files'
        ordering = ['-uploaded_at']
        
    def __str__(self):
        return f"{self.original_name} ({self.user.username})"
    
    @property
    def file_url(self):
        """Return the URL to access the file"""
        from django.conf import settings
        return f"{settings.MEDIA_URL}{self.file_path}"
    
    @property
    def formatted_size(self):
        """Return human readable file size"""
        if self.file_size == 0:
            return "0B"
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        size = self.file_size
        while size >= 1024 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
        return f"{size:.2f} {size_names[i]}"
    
    
class ArrayField(models.TextField):
    def from_db_value(self, value, expression, connection):
        """Converts a string representation of the array back to a numpy array."""
        if value is None:
            return value
        return np.fromstring(value[1:-1], sep=',')  # Converts from string back to np.array

    def to_python(self, value):
        """Converts a numpy array to string."""
        if isinstance(value, np.ndarray):
            return value
        return np.fromstring(value[1:-1], sep=',')  # Converting from string back to np.array

    def get_prep_value(self, value):
        """Converts a numpy array to a string for storage."""
        if isinstance(value, np.ndarray):
            return np.array2string(value, separator=',', prefix='', suffix='')  # Convert to string
        return value


class Signature(models.Model):
    uploaded_file_id = models.OneToOneField(UploadedFile, on_delete=models.CASCADE, related_name='file_data')
    signature_matrix = ArrayField()
    private_key_matrix = ArrayField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Signature created at {self.created_at}"

    class Meta:
        verbose_name = "Signature"
        verbose_name_plural = "Signatures"