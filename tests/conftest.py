from django.conf import settings


def pytest_configure():
    settings.configure(
        SECRET_KEY='undo',
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': 'ctrlz',
                'USER': 'ctrlz',
                'PASSWORD': 'ctrlz',
            },
            'secondary': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': 'ctrlz2',
                'USER': 'ctrlz',
                'PASSWORD': 'ctrlz',
            }
        }
    )
