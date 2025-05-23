from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import CustomUser, Book, Borrow, BorrowHistory


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)  # Get the default response from TokenObtainPairSerializer

        # Add custom data to the response (username, role)
        data['username'] = self.user.username
        data['role'] = self.user.role  # Assuming you have a role field in your User model

        return data

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'role']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = CustomUser.objects.create_user(**validated_data)
        return user

class BookSerializer(serializers.ModelSerializer):
    borrowed_by = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = '__all__'  # include borrowed_by field dynamically

    def get_borrowed_by(self, obj):
        borrow = obj.borrow_set.filter(return_date__isnull=True).first()
        if borrow:
            return borrow.user.username
        return None

class BorrowSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    book_title = serializers.CharField(source='book.title', read_only=True)
    class Meta:
        model = Borrow
        fields = '__all__'
        
    def get_borrowed_by(self, obj):
        borrow = obj.borrow_set.filter(return_date__isnull=True).first()
        print("------------------------", borrow)
        return borrow.user.username if borrow else None


class BorrowHistorySerializer(serializers.ModelSerializer):
    book = BookSerializer()
    book_title = serializers.CharField(source='book.title', read_only=True)
    book_image = serializers.SerializerMethodField()
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = BorrowHistory
        fields = ['id', 'book_title', 'book_image', 'username', 'borrow_date', 'return_date', 'image']

    def get_book_image(self, obj):
        request = self.context.get('request')
        if obj.book.image:
            return request.build_absolute_uri(obj.book.image.url)
        return None
