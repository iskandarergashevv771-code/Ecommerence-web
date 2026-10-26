from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User

# Create your models here.
# Modellar malumotlar bazasida admin panelga
class Catgeory(models.Model):
    nomi = models.CharField(max_length=200)
    def __str__(self):
        return self.nomi
    
class Member(models.Model):
    ism = models.CharField("Ism",max_length=20)
    familiya = models.CharField("Familiya",max_length=25)
    yosh = models.IntegerField(null=True)
    email = models.EmailField("Email") 

class Product(models.Model):
    name = models.CharField("Mahsulot nomi",max_length=200)
    narxi = models.IntegerField("Narx")
    tavsifi = models.TextField("Holati")
    image = models.ImageField(upload_to="media")
    miqdori = models.IntegerField(null=True)
    korishlar = models.PositiveIntegerField(default=0)
    likes = models.ManyToManyField(User, related_name="likes_products", blank=True)

    def like_soni(self):
        return self.likes.count()

    category = models.ForeignKey(Catgeory,on_delete=models.CASCADE,blank=True,null=True)

    slug = models.SlugField(unique=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Review(models.Model):
    # Maydon nomi 'mahsulot' ekanligiga e'tibor bering
    mahsulot = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, f"{i} Yulduz") for i in range(1, 6)], default=5, verbose_name="Reyting")
    comment = models.TextField(verbose_name="Izoh")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Sana")

    def __str__(self):
        return f"{self.user.username} - {self.mahsulot.name} ({self.rating}⭐️)"

class Wishlist(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name = 'wishlist')
    products = models.ForeignKey(Product,on_delete=models.CASCADE,related_name = 'wishlisted_by')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('user','products')

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # Xatolik to'g'irlandi: matn bir qatorga keltirildi
        return f"Savat #{self.id} - {self.user.username if self.user else 'Mehmon'}"

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    mahsulot = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.mahsulot.name}"

    @property
    def total_price(self):
        return self.mahsulot.narxi * self.quantity

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())