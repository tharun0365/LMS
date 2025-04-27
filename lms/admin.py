from django.contrib import admin
from lms.models import CustomUser, Book, Borrow

admin.site.register(CustomUser)
admin.site.register(Book)
admin.site.register(Borrow)