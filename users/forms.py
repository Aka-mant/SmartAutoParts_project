from django import forms

from .models import Profile, User


PREFERRED_LANGUAGE_CHOICES = (
    ("", "Выберите язык"),
    ("Китайский (мандарин)", "Китайский (мандарин)"),
    ("Английский", "Английский"),
    ("Хинди", "Хинди"),
    ("Испанский", "Испанский"),
    ("Арабский", "Арабский"),
    ("Бенгальский", "Бенгальский"),
    ("Португальский", "Португальский"),
    ("Русский", "Русский"),
    ("Урду", "Урду"),
    ("Индонезийский", "Индонезийский"),
)


class UserProfileUpdateForm(forms.ModelForm):
    """
    Форма редактирования основной информации пользователя.

    Позволяет изменить имя пользователя, email,
    имя, фамилию и аватар.
    """

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "avatar",
        )
        widgets = {
            "username": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Введите имя пользователя",
                    "autocomplete": "username",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Введите email",
                    "autocomplete": "email",
                }
            ),
            "first_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Введите имя",
                    "autocomplete": "given-name",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Введите фамилию",
                    "autocomplete": "family-name",
                }
            ),
            "avatar": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/*",
                }
            ),
        }

    def clean_email(self):
        """
        Проверяет уникальность email,
        исключая текущего пользователя.
        """
        email = self.cleaned_data["email"].strip().lower()

        email_exists = (
            User.objects
            .exclude(pk=self.instance.pk)
            .filter(email__iexact=email)
            .exists()
        )

        if email_exists:
            raise forms.ValidationError(
                "Пользователь с таким email уже существует."
            )

        return email

    def clean_username(self):
        """
        Проверяет уникальность имени пользователя,
        исключая текущего пользователя.
        """
        username = self.cleaned_data["username"].strip()

        username_exists = (
            User.objects
            .exclude(pk=self.instance.pk)
            .filter(username__iexact=username)
            .exists()
        )

        if username_exists:
            raise forms.ValidationError(
                "Пользователь с таким именем уже существует."
            )

        return username


class ProfileUpdateForm(forms.ModelForm):
    """
    Форма редактирования дополнительной информации профиля.

    Позволяет изменить место проживания,
    предпочитаемый язык, сведения об автомобиле
    и краткую информацию о пользователе.
    """

    preferred_language = forms.ChoiceField(
        label="Предпочитаемый язык",
        required=False,
        choices=PREFERRED_LANGUAGE_CHOICES,
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "autocomplete": "language",
            }
        ),
    )

    class Meta:
        model = Profile
        fields = (
            "country",
            "city",
            "preferred_language",
            "car_brand",
            "car_model",
            "car_year",
            "bio",
        )
        widgets = {
            "country": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Например: Россия",
                    "autocomplete": "country-name",
                }
            ),
            "city": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Например: Москва",
                    "autocomplete": "address-level2",
                }
            ),
            "car_brand": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Например: Toyota",
                }
            ),
            "car_model": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Например: Corolla",
                }
            ),
            "car_year": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Например: 2020",
                    "min": 1886,
                    "max": 2100,
                }
            ),
            "bio": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": (
                        "Расскажите немного о себе "
                        "и своём автомобиле"
                    ),
                    "rows": 6,
                }
            ),
        }

    def clean_car_year(self):
        """
        Проверяет корректность года выпуска автомобиля.
        """
        car_year = self.cleaned_data.get("car_year")

        if car_year is None:
            return car_year

        if car_year < 1886:
            raise forms.ValidationError(
                "Год выпуска автомобиля не может быть меньше 1886."
            )

        if car_year > 2100:
            raise forms.ValidationError(
                "Укажите корректный год выпуска автомобиля."
            )

        return car_year
    
