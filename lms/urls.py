from django.urls import path, re_path
from .views import RegisterView, BookView, BorrowReturnBookView, MeView, CustomTokenObtainPairView, BorrowHistoryView, YourBooksView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('me/', MeView.as_view(), name='me'),
     path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('register/', RegisterView.as_view()),
    path('login/', TokenObtainPairView.as_view()),

    path('token/refresh/', TokenRefreshView.as_view()),
    
    re_path(r'^books(?:/(?P<book_id>\d+))?/$', BookView.as_view(), name='book-view'),
    path('books/<int:book_id>/borrow-return/', BorrowReturnBookView.as_view(), name='borrow-return-book'),
    path('borrow-history/', BorrowHistoryView.as_view(), name='borrow-history'),
    path('your-books/', YourBooksView.as_view(), name='your-books'),
    
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)