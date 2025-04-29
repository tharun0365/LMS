
# from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.utils import timezone
from .serializers import RegisterSerializer, BookSerializer, CustomTokenObtainPairSerializer, BorrowHistorySerializer, BorrowSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import Book, Borrow, BorrowHistory


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = RegisterSerializer(request.user)
        print("serializer---------------------meView",serializer)
        return Response(serializer.data)

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'User registered successfully'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BookView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, book_id=None):
        if book_id:
            try:
                book = Book.objects.get(id=book_id)
                serializer = BookSerializer(book)
                return Response(serializer.data)
            except Book.DoesNotExist:
                return Response({'error': 'Book not found'}, status=status.HTTP_404_NOT_FOUND)
        else: 
            books = Book.objects.all()
            serializer = BookSerializer(books, many=True)
            return Response(serializer.data)

    def post(self, request):
        if request.user.role != 'librarian':
            return Response({'error': 'Only librarians can add books'}, status=status.HTTP_403_FORBIDDEN)
        serializer = BookSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, book_id):
        if request.user.role != 'librarian':
            return Response({'error': 'Only librarians can update books'}, status=status.HTTP_403_FORBIDDEN)
        try:
            book = Book.objects.get(id=book_id)
            serializer = BookSerializer(book, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Book.DoesNotExist:
            return Response({'error': 'Book not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, book_id):
        if request.user.role != 'librarian':
            return Response({'error': 'Only librarians can delete books'}, status=status.HTTP_403_FORBIDDEN)
        try:
            book = Book.objects.get(id=book_id)
            book.delete()
            return Response({'message': 'Book deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
        except Book.DoesNotExist:
            return Response({'error': 'Book not found'}, status=status.HTTP_404_NOT_FOUND)



class BorrowReturnBookView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, book_id):
        action = request.query_params.get('action')  # expects 'borrow' or 'return'
        print("action---------------------------------------------",action)
        print("request--------------------------------------------",request)
        print("self-----------------------------------------------",self)

        if action == 'borrow':
            try:
                book = Book.objects.get(id=book_id)
                print("book---------------",book)

             
                if not book.available:
                    return Response({'error': 'Book already borrowed'}, status=400)
                book.available = False
                book.save()                            
                print("---------------------------")
                Borrow.objects.create(user=request.user, book=book)
                return Response({'message': 'Book borrowed'}, status=200)
    
            except Book.DoesNotExist:
                return Response({'error': 'Book not found'}, status=404)

        elif action == 'return':
            try:
                borrow = Borrow.objects.get(book_id=book_id, user=request.user, return_date__isnull=True)
                print("borrow---------------------------------", borrow)
                borrow.return_date = timezone.now().date()
                borrow.save()
                borrow.book.available = True
                borrow.book.save()
                return Response({'message': 'Book returned'}, status=200)
            except Borrow.DoesNotExist:
                return Response({'error': 'Borrow record not found'}, status=404)

        else:
            return Response({'error': 'Invalid action. Use ?action=borrow or ?action=return'}, status=400)


class BorrowHistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role == 'librarian':  # if librarian, see all
            borrows = Borrow.objects.all()
        else:  # if member, see only their own
            borrows = Borrow.objects.filter(user=request.user)

        serializer = BorrowSerializer(borrows, many=True)
        return Response(serializer.data, status=200)