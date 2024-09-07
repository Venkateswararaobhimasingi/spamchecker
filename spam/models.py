from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class Message(models.Model):
    id = models.AutoField(primary_key=True)
    from_address = models.EmailField(max_length=254)  
    to_address = models.EmailField(max_length=254) 
    subject = models.CharField(max_length=150)  
    message_content = models.TextField()  
    date_sent = models.DateTimeField(default=timezone.now)  
    author = models.ForeignKey(User, on_delete=models.CASCADE)  
    is_read = models.BooleanField(default=False)  
    is_spam = models.BooleanField(default=False)  

    def save(self, *args, **kwargs):
        
        super().save(*args, **kwargs)

    def __str__(self):
       
        return f'Message from {self.from_address} to {self.to_address} - {self.subject}'
