from django.contrib import admin
from .models import User
from .models import *


admin.site.register(OTP)
admin.site.register(Cuisine)
admin.site.register(Rating)
admin.site.register(MenuItem)
admin.site.register(User)
admin.site.register(Child)
admin.site.register(UserToken)
