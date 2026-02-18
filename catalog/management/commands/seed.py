"""
Management command to seed the database with sample data.
Usage: uv run python manage.py seed
       uv run python manage.py seed --clear   (clears existing data first)
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal


class Command(BaseCommand):
    help = "Seed the database with sample categories, products, variants, discounts, and users."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing catalog/order/review data before seeding",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self._clear_data()

        self._create_users()
        categories = self._create_categories()
        products = self._create_products(categories)
        self._create_discounts(products)
        self._create_sample_orders(products)
        self.stdout.write(self.style.SUCCESS(">> Seed data created successfully!"))

    def _clear_data(self):
        from reviews.models import Review
        from orders.models import Order, Cart
        from catalog.models import Category, Product, Discount

        self.stdout.write("Clearing existing data...")
        Review.objects.all().delete()
        Order.objects.all().delete()
        Cart.objects.all().delete()
        Discount.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()
        self.stdout.write(self.style.WARNING("  >> Cleared"))

    def _create_users(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Admin / superuser
        if not User.objects.filter(phone="+218910000001").exists():
            User.objects.create_superuser(
                phone="+218910000001",
                password="admin1234",
                full_name="Store Owner",
                city="Tripoli",
            )
            self.stdout.write("  >> Superuser: +218910000001 / admin1234")

        # Sample customers
        customers = [
            {
                "phone": "+218920000001",
                "full_name": "Ahmed Al-Mansouri",
                "city": "Tripoli",
                "address": "Sharia Al-Fatah, Building 5, Apartment 12",
            },
            {
                "phone": "+218920000002",
                "full_name": "Fatima Benali",
                "city": "Benghazi",
                "address": "Sharia Omar Al-Mukhtar, Building 3",
            },
            {
                "phone": "+218920000003",
                "full_name": "Mohammed Zayed",
                "city": "Misrata",
                "address": "Sharia Al-Jazeera, Villa 7",
            },
        ]

        for c in customers:
            if not User.objects.filter(phone=c["phone"]).exists():
                User.objects.create_user(
                    phone=c["phone"],
                    password="customer1234",
                    **{k: v for k, v in c.items() if k != "phone"},
                )
        self.stdout.write(f"  >> {len(customers)} sample customers created (password: customer1234)")

    def _create_categories(self):
        from catalog.models import Category

        cats_data = [
            {"name": "Clothing", "order": 1, "description": "Men's and women's fashion"},
            {"name": "Electronics", "order": 2, "description": "Phones, accessories, and gadgets"},
            {"name": "Home & Kitchen", "order": 3, "description": "Furniture, cookware, and decor"},
            {"name": "Beauty & Care", "order": 4, "description": "Skincare, cosmetics, and personal care"},
            {"name": "Sports & Outdoors", "order": 5, "description": "Sports equipment and outdoor gear"},
        ]

        categories = {}
        for data in cats_data:
            cat, _ = Category.objects.get_or_create(
                name=data["name"],
                defaults={
                    "description": data["description"],
                    "order": data["order"],
                    "is_active": True,
                },
            )
            categories[data["name"]] = cat

        # Sub-categories
        sub_cats = [
            {"name": "Men's Clothing", "parent": "Clothing", "order": 1},
            {"name": "Women's Clothing", "parent": "Clothing", "order": 2},
            {"name": "Phone Accessories", "parent": "Electronics", "order": 1},
        ]
        for sub in sub_cats:
            Category.objects.get_or_create(
                name=sub["name"],
                defaults={
                    "parent": categories[sub["parent"]],
                    "order": sub["order"],
                    "is_active": True,
                },
            )

        self.stdout.write(f"  >> {len(cats_data)} categories + sub-categories created")
        return categories

    def _create_products(self, categories):
        from catalog.models import Product, ProductVariant, VariantType, VariantOption

        products_data = [
            # Clothing
            {
                "name": "Classic Linen Shirt",
                "category": "Clothing",
                "base_price": Decimal("85.00"),
                "description": "Comfortable and breathable linen shirt, perfect for summer.",
                "is_featured": True,
                "variants": {
                    "types": ["Color", "Size"],
                    "combinations": [
                        {"Color": "White", "Size": "S", "stock": 10},
                        {"Color": "White", "Size": "M", "stock": 15},
                        {"Color": "White", "Size": "L", "stock": 8},
                        {"Color": "Blue", "Size": "S", "stock": 5},
                        {"Color": "Blue", "Size": "M", "stock": 12},
                        {"Color": "Blue", "Size": "L", "stock": 7},
                        {"Color": "Beige", "Size": "M", "stock": 6},
                        {"Color": "Beige", "Size": "L", "stock": 9},
                    ],
                },
            },
            {
                "name": "Slim Fit Jeans",
                "category": "Clothing",
                "base_price": Decimal("120.00"),
                "description": "Modern slim-fit jeans made from premium denim.",
                "is_featured": True,
                "variants": {
                    "types": ["Color", "Waist Size"],
                    "combinations": [
                        {"Color": "Dark Blue", "Waist Size": "30", "stock": 8},
                        {"Color": "Dark Blue", "Waist Size": "32", "stock": 12},
                        {"Color": "Dark Blue", "Waist Size": "34", "stock": 6},
                        {"Color": "Black", "Waist Size": "30", "stock": 5},
                        {"Color": "Black", "Waist Size": "32", "stock": 10},
                        {"Color": "Black", "Waist Size": "34", "stock": 4},
                    ],
                },
            },
            # Electronics
            {
                "name": "Wireless Bluetooth Earbuds",
                "category": "Electronics",
                "base_price": Decimal("180.00"),
                "description": "True wireless stereo earbuds with 24h battery life and noise cancellation.",
                "is_featured": True,
                "variants": {
                    "types": ["Color"],
                    "combinations": [
                        {"Color": "White", "stock": 20},
                        {"Color": "Black", "stock": 15},
                        {"Color": "Navy Blue", "stock": 8},
                    ],
                },
            },
            {
                "name": "Phone Case - iPhone Compatible",
                "category": "Electronics",
                "base_price": Decimal("35.00"),
                "description": "Shockproof silicone phone case with camera protection.",
                "variants": {
                    "types": ["Model", "Color"],
                    "combinations": [
                        {"Model": "iPhone 13", "Color": "Black", "stock": 25},
                        {"Model": "iPhone 13", "Color": "Clear", "stock": 20},
                        {"Model": "iPhone 14", "Color": "Black", "stock": 18},
                        {"Model": "iPhone 14", "Color": "Clear", "stock": 15},
                        {"Model": "iPhone 15", "Color": "Black", "stock": 22},
                        {"Model": "iPhone 15", "Color": "Clear", "stock": 18},
                    ],
                },
            },
            # Home & Kitchen
            {
                "name": "Stainless Steel Cookware Set",
                "category": "Home & Kitchen",
                "base_price": Decimal("320.00"),
                "description": "5-piece stainless steel cookware set. Dishwasher safe.",
                "is_featured": True,
                "variants": {
                    "types": ["Pieces"],
                    "combinations": [
                        {"Pieces": "3-Piece", "stock": 10, "price": Decimal("220.00")},
                        {"Pieces": "5-Piece", "stock": 8},
                        {"Pieces": "7-Piece", "stock": 5, "price": Decimal("420.00")},
                    ],
                },
            },
            {
                "name": "Memory Foam Pillow",
                "category": "Home & Kitchen",
                "base_price": Decimal("95.00"),
                "description": "Ergonomic memory foam pillow for better sleep posture.",
                "variants": {
                    "types": ["Size"],
                    "combinations": [
                        {"Size": "Standard", "stock": 30},
                        {"Size": "King", "stock": 15, "price": Decimal("120.00")},
                    ],
                },
            },
            # Beauty
            {
                "name": "Argan Oil Face Serum",
                "category": "Beauty & Care",
                "base_price": Decimal("75.00"),
                "description": "100% pure Moroccan argan oil serum. Anti-aging and moisturizing.",
                "is_featured": True,
                "variants": {
                    "types": ["Size"],
                    "combinations": [
                        {"Size": "30ml", "stock": 40},
                        {"Size": "60ml", "stock": 25, "price": Decimal("130.00")},
                    ],
                },
            },
            {
                "name": "Vitamin C Sunscreen SPF 50",
                "category": "Beauty & Care",
                "base_price": Decimal("55.00"),
                "description": "Lightweight sunscreen with Vitamin C brightening formula.",
                "variants": {
                    "types": ["Size"],
                    "combinations": [
                        {"Size": "50ml", "stock": 50},
                        {"Size": "100ml", "stock": 30, "price": Decimal("95.00")},
                    ],
                },
            },
            # Sports
            {
                "name": "Yoga Mat - Non-Slip",
                "category": "Sports & Outdoors",
                "base_price": Decimal("70.00"),
                "description": "6mm thick non-slip yoga mat with alignment lines.",
                "variants": {
                    "types": ["Color"],
                    "combinations": [
                        {"Color": "Purple", "stock": 20},
                        {"Color": "Blue", "stock": 18},
                        {"Color": "Black", "stock": 15},
                        {"Color": "Green", "stock": 12},
                    ],
                },
            },
            {
                "name": "Resistance Bands Set",
                "category": "Sports & Outdoors",
                "base_price": Decimal("45.00"),
                "description": "Set of 5 resistance bands for home workouts. Various resistance levels.",
                "is_featured": True,
                "variants": {
                    "types": ["Resistance Level"],
                    "combinations": [
                        {"Resistance Level": "Light (5-Pack)", "stock": 30},
                        {"Resistance Level": "Medium (5-Pack)", "stock": 25},
                        {"Resistance Level": "Heavy (5-Pack)", "stock": 20},
                        {"Resistance Level": "Mixed Set (5-Pack)", "stock": 35},
                    ],
                },
            },
        ]

        created_products = []

        for p_data in products_data:
            product, created = Product.objects.get_or_create(
                name=p_data["name"],
                defaults={
                    "category": categories[p_data["category"]],
                    "base_price": p_data["base_price"],
                    "description": p_data["description"],
                    "is_featured": p_data.get("is_featured", False),
                    "is_active": True,
                },
            )

            if created:
                # Create variant types and options
                variant_data = p_data.get("variants", {})
                type_objs = {}
                for i, type_name in enumerate(variant_data.get("types", [])):
                    vtype, _ = VariantType.objects.get_or_create(
                        product=product,
                        name=type_name,
                        defaults={"order": i},
                    )
                    type_objs[type_name] = vtype

                # Create all option values
                option_objs = {}  # (type_name, value) -> VariantOption
                for combo in variant_data.get("combinations", []):
                    for type_name in variant_data.get("types", []):
                        value = combo.get(type_name)
                        if value and (type_name, value) not in option_objs:
                            opt, _ = VariantOption.objects.get_or_create(
                                variant_type=type_objs[type_name],
                                value=value,
                            )
                            option_objs[(type_name, value)] = opt

                # Create variants
                for combo in variant_data.get("combinations", []):
                    price_override = combo.get("price")
                    variant = ProductVariant.objects.create(
                        product=product,
                        stock_qty=combo["stock"],
                        price_override=price_override,
                    )
                    # Assign options
                    options_to_add = []
                    for type_name in variant_data.get("types", []):
                        value = combo.get(type_name)
                        if value:
                            options_to_add.append(option_objs[(type_name, value)])
                    variant.options.set(options_to_add)

            created_products.append(product)

        self.stdout.write(f"  >> {len(products_data)} products with variants created")
        return created_products

    def _create_discounts(self, products):
        from catalog.models import Discount, Category

        now = timezone.now()

        # Discount on a specific product (Wireless Earbuds - 15% off)
        earbuds = next((p for p in products if "Earbuds" in p.name), None)
        if earbuds:
            Discount.objects.get_or_create(
                name="Earbuds Flash Sale",
                defaults={
                    "discount_type": Discount.DISCOUNT_TYPE_PERCENT,
                    "value": Decimal("15"),
                    "product": earbuds,
                    "start_date": now - timedelta(hours=1),
                    "end_date": now + timedelta(days=7),
                    "is_active": True,
                },
            )

        # Category-wide discount (Beauty & Care - 10% off)
        beauty_cat = Category.objects.filter(name="Beauty & Care").first()
        if beauty_cat:
            Discount.objects.get_or_create(
                name="Beauty Week Sale",
                defaults={
                    "discount_type": Discount.DISCOUNT_TYPE_PERCENT,
                    "value": Decimal("10"),
                    "category": beauty_cat,
                    "start_date": now - timedelta(hours=1),
                    "end_date": now + timedelta(days=14),
                    "is_active": True,
                },
            )

        # Fixed discount on a product (Cookware - 50 LYD off)
        cookware = next((p for p in products if "Cookware" in p.name), None)
        if cookware:
            Discount.objects.get_or_create(
                name="Kitchen Special",
                defaults={
                    "discount_type": Discount.DISCOUNT_TYPE_FIXED,
                    "value": Decimal("50"),
                    "product": cookware,
                    "start_date": now - timedelta(hours=1),
                    "end_date": now + timedelta(days=3),
                    "is_active": True,
                },
            )

        self.stdout.write("  >> 3 discounts created (1 flash sale, 1 category-wide, 1 fixed)")

    def _create_sample_orders(self, products):
        from django.contrib.auth import get_user_model
        from orders.models import Order, OrderItem, OrderStatusHistory

        User = get_user_model()
        customer = User.objects.filter(phone="+218920000001").first()
        if not customer or not products:
            return

        # Sample delivered order
        order1 = Order.objects.create(
            user=customer,
            status=Order.STATUS_DELIVERED,
            notes="Please wrap carefully",
            delivery_address=customer.address,
        )
        shirt = next((p for p in products if "Shirt" in p.name), None)
        if shirt:
            variant = shirt.variants.first()
            if variant:
                OrderItem.objects.create(
                    order=order1,
                    variant=variant,
                    quantity=2,
                    price_at_order=variant.effective_price(),
                )

        OrderStatusHistory.objects.create(order=order1, status=Order.STATUS_PENDING, note="Order placed")
        OrderStatusHistory.objects.create(order=order1, status=Order.STATUS_PROCESSING, note="Owner contacted customer")
        OrderStatusHistory.objects.create(order=order1, status=Order.STATUS_PAYMENT_RECEIVED, note="Payment confirmed")
        OrderStatusHistory.objects.create(order=order1, status=Order.STATUS_PACKING, note="Packing started")
        OrderStatusHistory.objects.create(order=order1, status=Order.STATUS_SHIPPED, note="Shipped via courier")
        OrderStatusHistory.objects.create(order=order1, status=Order.STATUS_DELIVERED, note="Delivered successfully")

        # Sample pending order
        order2 = Order.objects.create(
            user=customer,
            status=Order.STATUS_PENDING,
            delivery_address=customer.address,
        )
        earbuds = next((p for p in products if "Earbuds" in p.name), None)
        if earbuds:
            variant = earbuds.variants.first()
            if variant:
                OrderItem.objects.create(
                    order=order2,
                    variant=variant,
                    quantity=1,
                    price_at_order=variant.effective_price(),
                )

        OrderStatusHistory.objects.create(order=order2, status=Order.STATUS_PENDING, note="Order placed by customer")

        # Sample review on delivered product
        if shirt:
            from reviews.models import Review
            Review.objects.get_or_create(
                product=shirt,
                user=customer,
                defaults={
                    "rating": 5,
                    "title": "Excellent quality!",
                    "body": "Very comfortable shirt, great fabric quality. Will definitely order again.",
                    "claimed_order_id": order1.pk,
                    "is_verified_purchase": True,
                    "is_approved": True,
                },
            )

        self.stdout.write("  >> 2 sample orders + 1 review created for Ahmed Al-Mansouri")
