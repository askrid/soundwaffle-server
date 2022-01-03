from rest_framework.exceptions import APIException, ValidationError
from rest_framework import permissions, status
from rest_framework.pagination import PageNumberPagination
from django.conf import settings
from guardian.shortcuts import assign_perm
import boto3, os, re

MODEL_NAMES = ('track', 'set', 'user',)
FIELD_NAMES = ('audio', 'image', 'image_profile', 'image_header',)
MEDIA_PATHS = {
    'track': {
        'audio': settings.S3_BASE_URL + settings.S3_MUSIC_TRACK_DIR,
        'image': settings.S3_BASE_URL + settings.S3_IMAGES_TRACK_DIR,
    },
    'set': {
        'image': settings.S3_BASE_URL + settings.S3_IMAGES_SET_DIR,
    },
    'user': {
        'image_profile': settings.S3_BASE_URL + settings.S3_IMAGES_USER_PROFILE_DIR,
        'image_header': settings.S3_BASE_URL + settings.S3_IMAGES_USER_HEADER_DIR,
    },
}
MEDIA_TYPES = ('audio', 'image',)
EXTENSIONS = {
    'audio': ('.wav', '.flac', '.aiff', '.alac', 'mp3', '.aac', '.ogg', '.oga', '.mp4', '.mp2', '.m4a', '.3gp', '.3g2', '.mj2', '.amr', '.wma',),
    'image': ('.jpg', '.png',),
}
FILENAME_PATTERN = re.compile('^[a-zA-Z0-9\/\!\-\_\.\*\'\(\)]+$')


def get_presigned_url(url, method, full_url=True):
    if url is None:
        return None

    if method not in [ 'get_object', 'put_object' ]:
        raise ValueError("method choices: ('get_object', 'put_object')")

    if full_url:
        key = url.replace(settings.S3_BASE_URL, '')

    presigned_url = boto3.client(
        's3',
        region_name=settings.S3_REGION_NAME,
        aws_access_key_id=settings.AWS_ACCESS_KEY,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    ).generate_presigned_url(
        ClientMethod=method,
        Params={
            'Bucket': settings.S3_BUCKET_NAME,
            'Key': key,
        },
        ExpiresIn=300
    )

    return presigned_url


def assign_object_perms(user, instance):
    """
    Assigns permission to modify and delete the instance to the user.
    """
    kwargs = {
        'app_label': instance._meta.app_label,
        'model_name': instance._meta.model_name
    }

    assign_perm('%(app_label)s.change_%(model_name)s' % kwargs, user, instance)
    assign_perm('%(app_label)s.delete_%(model_name)s' % kwargs, user, instance)


class CustomObjectPermissions(permissions.IsAuthenticatedOrReadOnly, permissions.DjangoObjectPermissions):
    pass


class ConflictError(APIException):
    
    status_code = status.HTTP_409_CONFLICT
    default_detail = ('Already existing name.')
    default_code = 'conflict'


class MediaUploadMixin:
    """
    Must be used with 'rest_framework.serializers.ModelSerializer'.
    """

    def _get_unique_url(self, filename, model_name, field_name, queryset=None):
        if filename is None:
            return None

        try:
            url = MEDIA_PATHS[model_name][field_name] + filename
        except KeyError:
            raise ValueError(f"model_name choices: {MODEL_NAMES}, field_name choices: {FIELD_NAMES}")

        queryset = queryset or self.Meta.model.objects.exclude(id=getattr(self.instance, 'id', None))
        name, ext = os.path.splitext(url)

        while queryset.filter(**{field_name: url}).exists():
            if re.search(r'\-\d+$', name):
                num = re.search(r'\d+$', name).group(0)
                name = re.sub(r'\d+$', str(int(num)+1), name)
            else:
                name += '-1'
            url = name + ext
        
        return url

    def _get_presigned_url(self, instance, field_name):
        if self.context['request'].data.get(field_name+'_filename') is None:
            return None

        return get_presigned_url(getattr(instance, field_name, None), 'put_object')

    def _validate_filename(self, value, media_type):
        if not self.check_extension(value, media_type):
            raise ValidationError(f"Unsupported {media_type} file extension.")

        if not self.check_filename(value):
            raise ValidationError(f"Incorrect {media_type} filename format.")

        return value

    def get_unique_urls(self, **kwargs):

        data = {}
        for key, filename in kwargs.items():
            if not key.endswith('_filename'):
                continue
            field_name = key.replace('_filename', '')
            url = self._get_unique_url(filename, self.Meta.model._meta.model_name, field_name)
            if url is not None:
                data[field_name] = url

        return data

    def get_audio_presigned_url(self, instance):
        return self._get_presigned_url(instance, 'audio')

    def get_image_presigned_url(self, instance):
        return self._get_presigned_url(instance, 'image')

    def get_image_profile_presigned_url(self, instance):
        return self._get_presigned_url(instance, 'image_profile')

    def get_image_header_presigned_url(self, instance):
        return self._get_presigned_url(instance, 'image_header')

    def validate_audio_filename(self, value):
        return self._validate_filename(value, 'audio')

    def validate_image_filename(self, value):
        return self._validate_filename(value, 'image')

    def validate_image_profile_filename(self, value):
        return self._validate_filename(value, 'image')

    def validate_image_header_filename(self, value):
        return self._validate_filename(value, 'image')

    @staticmethod
    def check_extension(filename, media_type):
        try:
            valid_extensions = EXTENSIONS[media_type]
        except KeyError:
            raise ValueError(f"media_type choices: {MEDIA_TYPES}")

        return filename.lower().endswith(valid_extensions)

    @staticmethod
    def check_filename(filename):

        return re.search(FILENAME_PATTERN, filename)

class ReactionUserListPagination(PageNumberPagination):
    page_size = 6
