from .base import *
import dj_database_url

USE_CLOUDINARY = True

SECRET_KEY = os.getenv("SECRET_KEY")
# DEBUG = True
DEBUG = os.getenv("DEBUG", "False") == "True"

allowed_hosts_env = os.getenv("ALLOWED_HOSTS", "127.0.0.1")
ALLOWED_HOSTS = [host.strip() for host in allowed_hosts_env.split(",") if host.strip()]

DATABASES = {
    'default': dj_database_url.parse(os.getenv("DATABASE_URL"))
}





print("DEBUG: ALLOWED_HOSTS env raw =", os.getenv("ALLOWED_HOSTS"))
print("DEBUG: ALLOWED_HOSTS parsed =", ALLOWED_HOSTS)

# CLOUDINARY_STORAGE = {
#     'CLOUD_NAME': env('CLOUD_NAME'),
#     'API_KEY': env('API_KEY'),
#     'API_SECRET': env('API_SECRET')
# }
# CLOUDINARY_STORAGE = {
#     'CLOUD_NAME': env('CLOUDINARY_CLOUD_NAME'),
#     'API_KEY': env('CLOUDINARY_API_KEY'),
#     'API_SECRET': env('CLOUDINARY_API_SECRET'),
# }

STORAGES = {
    'default': {
        'BACKEND': 'cloudinary_storage.storage.MediaCloudinaryStorage',
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}