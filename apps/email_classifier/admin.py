from django.contrib import admin
from .models import (
    Department, 
    DepartmentMail,
    Email,
    DraftResponse
)

admin.site.register(Department)
admin.site.register(DepartmentMail)
admin.site.register(Email)
admin.site.register(DraftResponse)