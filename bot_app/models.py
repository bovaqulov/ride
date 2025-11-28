from django.db import models

class BotClient(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=200, null=True, blank=True)
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=50, null=True, blank=True)
    language = models.CharField(max_length=50, default="uz")
    is_active = models.BooleanField(default=True)
    is_banned = models.BooleanField(default=False)
    total_rides = models.IntegerField(default=0)
    rating = models.IntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name

    class Meta:
        ordering = ['-created_at']

class TravelClass(models.TextChoices):
    ECONOMY = "economy", "Economy"
    STANDARD = "standard", "Standard"
    BUSINESS = "business", "Business"

class TravelStatus(models.TextChoices):
    CREATED = "created", "Created"
    ENDED = "ended", "Ended"
    REJECTED = "rejected", "Rejected"


class PassengerTravel(models.Model):
    user = models.BigIntegerField()
    from_location = models.CharField(max_length=200)
    to_location = models.CharField(max_length=200)
    travel_class = models.CharField(max_length=200, choices=TravelClass.choices, default=TravelClass.STANDARD)
    passenger = models.IntegerField(default=1)
    price = models.IntegerField(default=0)
    has_woman = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=TravelStatus.choices, default=TravelStatus.CREATED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.travel_class

    class Meta:
        ordering = ['-created_at']


class PassengerPost(models.Model):
    user = models.BigIntegerField()
    from_location = models.CharField(max_length=200)
    to_location = models.CharField(max_length=200)
    price = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=TravelStatus.choices, default=TravelStatus.CREATED)

    def __str__(self):
        return f"{self.from_location} -> {self.to_location}"

    class Meta:
        ordering = ['-created_at']

class DriverStatus(models.TextChoices):
    OFFLINE = "offline", "Offline"
    ONLINE = "online", "Online"

class Driver(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    from_location = models.CharField(max_length=200)
    to_location = models.CharField(max_length=200)
    status = models.CharField(max_length=10, choices=DriverStatus.choices, default=DriverStatus.OFFLINE)
    amount = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.from_location

    class Meta:
        ordering = ['-created_at']

class Car(models.Model):
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name="driver")
    car_number = models.CharField(max_length=200, unique=True)
    car_model = models.CharField(max_length=200)
    car_color = models.CharField(max_length=200)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.car_number

    class Meta:
        ordering = ['-created_at']


class DriverTransaction(models.Model):

    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
    amount = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.driver
    class Meta:
        ordering = ['-created_at']


class City(models.Model):
    title = models.CharField(max_length=200)
    subcategory = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True)
    translate = models.JSONField(null=True, blank=True)
    is_allowed = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title