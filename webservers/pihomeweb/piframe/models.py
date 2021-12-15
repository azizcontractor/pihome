from io import BytesIO

from django.core.files import File
from django.db import models

# Create your models here.
from PIL import Image

from .validators import validate_img_extension

from colorthief import ColorThief

MAX_SIZE = (1400, 1000)


class Slide(models.Model):
    title = models.CharField(max_length=32)
    image = models.ImageField(upload_to="images/", validators=[validate_img_extension])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        resize_image(self.image)


def resize_image(image):
    im = Image.open(image.path)
    im.thumbnail(MAX_SIZE, Image.ANTIALIAS)
    im.save(image.path, format=im.format)
