from django.db import models
from django.contrib.auth.models import User
from PIL import Image

from chemstats.utils.storage import s3_profile_image_retrieve, s3_get_random_default_image

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    group = models.ForeignKey('Group', on_delete=models.SET_NULL, null=True, blank=True)

    # Randomly select a default image from the default_images folder
    def default_image():
        return s3_get_random_default_image()

    image = models.ImageField(default=default_image, upload_to='profile_pics')
    
    def __str__(self):
        return f'{self.user.username} Profile'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Load image from S3 using the s3_profile_image_retrieve method
        file_obj = s3_profile_image_retrieve(self.image.name, as_path=True)
        img = Image.open(file_obj)

        # Crop the the image to a square centered on the image
        if img.height > img.width:
            left = 0
            top = (img.height - img.width) / 2
            right = img.width
            bottom = top + img.width
        else:
            left = (img.width - img.height) / 2
            top = 0
            right = left + img.height
            bottom = img.height
        img = img.crop((left, top, right, bottom))

        # Resize the image to 300x300 to save space
        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)

        # Convert the image to RGB if it's in RGBA mode
        if img.mode == 'RGBA':
            img = img.convert('RGB')

        # Save the image back to S3 using the s3_profile_image_store method
        from chemstats.utils.storage import s3_profile_image_store
        s3_profile_image_store(self.image.name, img)

class Group(models.Model):
    name = models.CharField(max_length=100)
    institution = models.CharField(max_length=100)
    admin = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.name} ({self.institution})'
