from django.shortcuts import render, redirect,get_object_or_404
from .models import Member, Product,Catgeory,Review,Wishlist,Cart,CartItem
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q,F,Avg
from django.views.decorators.http import require_POST
from .forms import RegisterForm, ReviewForm
from django.contrib.auth.decorators import login_required

def index(request):
    member = Product.objects.all()
    korilganlar = request.session.get("korilgan", [])

    context = {
        "mahsulot" : member
    }
    return render(request, "index.html",context)

def products(request, slug=None):
    # Agar slug berilgan bo'lsa bitta mahsulot olinadi
    if slug:
        product_item = get_object_or_404(Product, slug=slug)
        
        # Sharhlar va reyting faqat bitta mahsulot uchun ishlaydi
        reviews = product_item.reviews.all().order_by('-created_at')
        average_rating = reviews.aggregate(Avg('rating'))['rating__avg']

        if average_rating:
            average_rating = round(average_rating, 1)
        else:
            average_rating = 0

        # Izoh yuborish (POST) so'rovi
        if request.method == "POST":
            if not request.user.is_authenticated:
                messages.error(request, "Ro'yxatdan o'tishingiz kerak")
                return redirect('login')
            
            form = ReviewForm(request.POST)
            if form.is_valid():
                review = form.save(commit=False)
                review.mahsulot = product_item  # Modelga mos ravishda 'mahsulot' ishlatildi
                review.user = request.user
                review.save()
                messages.success(request, "Sharhingiz uchun rahmat")
                return redirect('product', slug=product_item.slug)
        else:
            form = ReviewForm()

        # Ko'rishlar sonini oshirish (Session orqali)
        korilganlar = request.session.get("korilgan", [])
        if product_item.id not in korilganlar:
            Product.objects.filter(id=product_item.id).update(korishlar=F("korishlar") + 1)
            korilganlar.append(product_item.id)
            request.session["korilgan"] = korilganlar
            product_item.refresh_from_db()

        liked = request.user.is_authenticated and product_item.likes.filter(id=request.user.id).exists()

        context = {
            "products": product_item,
            "average_rating": average_rating,
            "reviews": reviews,
            "form": form,
            "liked": liked,
        }
        return render(request, "product.html", context)

    else:
        # Agar slug berilmagan bo'lsa - barcha mahsulotlar ro'yxati chiqadi (Qidiruv bilan)
        all_products = Product.objects.all()
        query = request.GET.get("q")
        if query:
            all_products = all_products.filter(
                Q(name__icontains=query) | Q(tavsifi__icontains=query)
            )

        context = {
            "products": all_products,
            "query": query,
        }
        # Bu yerda barcha mahsulotlar chiqadigan shablonni qaytarishingiz mumkin (masalan: "product_list.html")
        return render(request, "product.html", context)

def login_form(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request,username = username,password=password)
        if user is not None:
            login(request,user)
            print("Ro'yxatdan o'tdiz")
            messages.success(request, "Royxatdan muvaffaqiyatli otdingiz")
            return redirect("index")
        else:
            print("Xato login parol !!!")
            return redirect("login")
    else:
        return render(request, "login.html")

def register_view(request):
    return render(request, "register.html")

def register_view(request):
    if request.method == "POST" :
        form = RegisterForm(request.POST)
        if form. is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            User.objects.create_user(
                username=username,
                password=password
            )
            messages.success(request, "Muvaffaqiyatli ro'yxatdan o'tdingiz")
            return redirect('login')
        else:
            messages.error(request, "Forma notogri toldirildi")
    else:
        form = RegisterForm()
        return render(request, "register.html", {'form': form})

# Create your views here.

def logout_view(request):
    logout(request)
    messages.success(request, "Siz tizimdan chiqdingiz")
    return redirect("index")

def like_view(request, slug):
    mahsulot = get_object_or_404(Product, slug=slug)

    if mahsulot.likes.filter(id=request.user.id).exists():
        mahsulot.likes.remove(request.user)   # like olib tashlash
    else:
        mahsulot.likes.add(request.user)      # like qo'yish

    # Qaysi sahifadan bosilgan bo'lsa, shu yerga qaytadi
    return redirect(request.META.get("HTTP_REFERER", "index"))

@login_required
def wishlist_list(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('products')
    context = {
        'wishlist_items' : wishlist_items
    }
    return render(request, 'wishlist.html',context)

@login_required
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist_item , created = Wishlist.objects.get_or_create(user=request.user,product=product)

    if not created:
        wishlist_list.delete()
        added = False
    else:
        added = True

    return redirect(request.META.get('HTTP_REFERER','wishlist_list'))

def cart_qism(request):
    if request.user.is_authenticated:
        cart , _ = Cart.objects.get_or_create(user = request.user)
    else:
        cart_id = request.session.get('cart_id')
        if cart_id:
            cart = Cart.objects.filter(id=cart_id,user = None).first()
            if not cart:
                cart = Cart.objects.create()
                request.session['cart_id'] = cart_id
        else:
            cart = Cart.objects.create()
            request.session['cart_id'] = cart.id
    return cart

def add_to_cart(request,slug):
    mahsulot = get_object_or_404(Product, slug=slug)
    cart = cart_qism(request)

    cart_item , created = CartItem.objects.get_or_create(cart=cart, mahsulot=mahsulot)
    if not created:
        cart_item.quantity = F('quantity') + 1
        cart_item.save()

    messages.success(request, "Savatchaga qo'shildi")
    return redirect(request.META.get("HTTP_REFERER", "index"))

def cart_detail(request):
    cart = cart_qism(request)
    context = {
        'cart' : cart
    }
    return render(request, "cart.html",context)

def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart_item.delete()
    messages.success(request, "Mahsulot savatdan olib tahlandi.")
    return redirect('cart_detail')