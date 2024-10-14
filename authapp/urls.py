from django.urls import path
from .views import *

urlpatterns = [
    # OTP API's
    path("sendotp", SendOTPView.as_view(), name="sendotp"),
    path("verifyotp", VerifyOTPView.as_view(), name="verifyotp"),
    # Child API's
    path("addchild", ChildAPIView.as_view(), name="addchild"),
    path("updatechild/<int:pk>/", ChildAPIView.as_view(), name="updatechild"),
    path("deletechild/<int:pk>/", ChildAPIView.as_view(), name="deletechild"),
    path("viewchild", ChildAPIView.as_view(), name="viewchild"),
    path("viewchild/<int:pk>/", ChildAPIView.as_view(), name="viewchild"),
    # Personal Detail API's
    path(
        "userpersonaldetail/<str:mobile>/",
        UserPersonalDetailAPIView.as_view(),
        name="userpersonaldetail",
    ),
    # User Status API's
    path("checkuser/<str:mobile>/", RetrieveUserAPIView.as_view(), name="checkuser"),
    # Menu Item API's
    path("listmenuitem", MenuItemAPIView.as_view(), name="listmenuitem"),
    path(
        "retrievemenuitem/<int:pk>/",
        MenuItemAPIView.as_view(),
        name="retrievemenuitem",
    ),
    path("updatemenuitem/<int:pk>/", MenuItemAPIView.as_view(), name="updatemenuitem"),
    path("createmenu", MenuItemAPIView.as_view(), name="createmenu"),
    # Ratings API's
    path("createrating", RatingAPIView.as_view(), name="creatrating"),
    path("listrating/<int:pk>/", RatingAPIView.as_view(), name="listrating"),
    path("deleterating/<int:pk>/", RatingAPIView.as_view(), name="deleterating"),
    # Cuisine API's
    path("addcuisine", CuisineAPIView.as_view(), name="addcuisine"),
    path("deletecuisine/<int:pk>/", CuisineAPIView.as_view(), name="deletecuisine"),
    path("listcuisine", CuisineAPIView.as_view(), name="listcuisine"),
    # Cart API's
    path("addtocart", CartAPIView.as_view(), name="addtocart"),
    path("cart/", CartAPIView.as_view(), name="cart"),
    path("cartupdate/<int:pk>/", CartAPIView.as_view(), name="cartupdate"),
    path("cartretrieve/<int:pk>/", CartAPIView.as_view(), name="cartretrieve"),
    path("deletecartitem/<int:pk>/", CartAPIView.as_view(), name="deletecartitem"),
    # Order API's
    path("order", OrderView.as_view(), name="order"),
    path("createorder", OrderView.as_view(), name="createorder"),
    path("updateorder/<str:pk>/", OrderView.as_view(), name="updateorder"),
    # Plan API's
    path("createplan", PlanAPIView.as_view(), name="createplan"),
    path("viewplan", PlanAPIView.as_view(), name="viewplan"),
    path("retrieveplan/<int:pk>/", PlanAPIView.as_view(), name="retrieveplan"),
    path("updateplan/<int:pk>/", PlanAPIView.as_view(), name="updateplan"),
    path("deleteplan/<int:pk>/", PlanAPIView.as_view(), name="deleteplan"),
    # Payment API's
    path("pay", PaymentAPIView.as_view(), name="pay"),
    # Subscription API's
    path("listsubscription", SubscriptionAPIView.as_view(), name="listsubscription"),
    path(
        "createsubscription", SubscriptionAPIView.as_view(), name="createsubscription"
    ),
    # Transaction Detail
    path("viewtransaction", TransactionDetailAPIView.as_view(), name="viewtransaction"),
    path("handlePayment", PaymentHandlerView.as_view(), name="handlepayment"),
]
