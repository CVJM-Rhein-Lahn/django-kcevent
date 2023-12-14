from django.contrib import admin

def custom_list_title_filter(title):
    class Wrapper(admin.AllValuesFieldListFilter):
        def __new__(cls, *args, **kwargs):
            instance = admin.AllValuesFieldListFilter(*args, **kwargs)
            instance.title = title
            return instance
    return Wrapper