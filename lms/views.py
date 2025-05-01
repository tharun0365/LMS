
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
            serializer = BookSerializer(data=request.data)
            print('post-----------------',serializer)
            if serializer.is_valid():
                book = serializer.save()
                return Response(BookSerializer(book).data, status=201)
            return Response(serializer.errors, status=400)

    def put(self, request, book_id):
        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response({'error': 'Book not found'}, status=404)

        serializer = BookSerializer(book, data=request.data, partial=True)
        if serializer.is_valid():
            updated_book = serializer.save()
            return Response(BookSerializer(updated_book).data, status=200)
        return Response(serializer.errors, status=400)
                        
    def delete(self, request, book_id):
        if request.user.role != 'librarian':
            return Response({'error': 'Only librarians can delete books'}, status=status.HTTP_403_FORBIDDEN)
        try:
            book = Book.objects.get(id=book_id)
            book.delete()
            return Response({'message': 'Book deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
        except Book.DoesNotExist:
            return Response({'error': 'Book not found'}, status=status.HTTP_404_NOT_FOUND)
        

class YourBooksView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        borrowed_books = Borrow.objects.filter(user=request.user, return_date__isnull=True)
        books = [borrow.book for borrow in borrowed_books]
        return Response(BookSerializer(books, many=True).data)


class BorrowReturnBookView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, book_id):
        action = request.query_params.get('action')  # expects 'borrow' or 'return'

        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response({'error': 'Book not found'}, status=status.HTTP_404_NOT_FOUND)

        if action == 'borrow':
            if book.available_copies <= 0:
                return Response({'error': 'No available copies to borrow'}, status=status.HTTP_400_BAD_REQUEST)

            # Prevent duplicate borrow if already borrowed and not returned
            already_borrowed = Borrow.objects.filter(book=book, user=request.user, return_date__isnull=True).exists()
            if already_borrowed:
                return Response({'error': 'You have already borrowed this book'}, status=400)

            book.available_copies -= 1
            book.save()
            Borrow.objects.create(user=request.user, book=book)
            return Response({'message': 'Book borrowed successfully'}, status=200)

        elif action == 'return':
            try:
                borrow = Borrow.objects.get(book=book, user=request.user, return_date__isnull=True)
            except Borrow.DoesNotExist:
                return Response({'error': 'Borrow record not found'}, status=status.HTTP_404_NOT_FOUND)

            borrow.return_date = timezone.now().date()
            borrow.save()
            book.available_copies += 1
            book.save()
            return Response({'message': 'Book returned successfully'}, status=200)

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