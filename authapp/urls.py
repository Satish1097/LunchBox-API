from django.urls import path
from .views import *

urlpatterns = [
    path("sendotp", SendOTPView.as_view(), name="sendotp"),
    path("verifyotp", VerifyOTPView.as_view(), name="verifyotp"),
    path("addchild", CreateChildAPIView.as_view(), name="addchild"),
    path(
        "userpersonaldetail/<str:mobile>/",
        UserPersonalDetailAPIView.as_view(),
        name="userpersonaldetail",
    ),
    path("checkuser/<str:mobile>/", RetrieveUserAPIView.as_view(), name="checkuser"),
    path("viewchild", ListChildAPIView.as_view(), name="viewchild"),
    path("listcuisine", ListCuisineAPIView.as_view(), name="listcuisine"),
    path("listmenuitem", ListMenuItemAPIView.as_view(), name="listmenuitem"),
    path(
        "retrievemenuitem/<int:pk>/",
        ListMenuItemAPIView.as_view(),
        name="retrievemenuitem",
    ),
    path(
        "updatemenuitem/<int:pk>/", MenuItemCreateView.as_view(), name="updatemenuitem"
    ),
    path("createrating/<int:pk>/", CreateRatingAPIView.as_view(), name="creatrating"),
    path("updatechild/<int:pk>/", UpdateChildAPIView.as_view(), name="updatechild"),
    path("addcuisine", AddCuisineAPIView.as_view(), name="addcuisine"),
    path("addcuisine/<int:pk>/", AddCuisineAPIView.as_view(), name="addcuisine"),
    path("createmenu", MenuItemCreateView.as_view(), name="createmenu"),
    path("addtocart", AddtoCartAPIView.as_view(), name="addtocart"),
]
