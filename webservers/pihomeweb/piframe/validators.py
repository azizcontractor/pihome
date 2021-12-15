def validate_img_extension(value):
    from pathlib import Path
    from django.core.exceptions import ValidationError

    allowed_exts = [".jpg", ".jpeg", ".png", ".apng", ".avif", ".svg", ".gif", ".webp"]
    ext = Path(value.path).suffix
    if ext.lower() not in allowed_exts:
        raise ValidationError(f"Unsupported File extension {ext}")
