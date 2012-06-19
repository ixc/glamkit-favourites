from django.conf import settings

settings = {
    'FAVOURITES_REDIRECT_IF_NO_PERMISSION': getattr(settings, 'FAVOURITES_REDIRECT_IF_NO_PERMISSION', None),
}