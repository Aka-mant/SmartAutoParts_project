from django import forms


class PartImageAnalysisUploadForm(forms.Form):
    """Загрузка фотографии для автоматической проверки и распознавания."""

    image = forms.ImageField(
        label="Фотография запчасти или инструмента",
        help_text=(
            "JPEG, PNG, WEBP или статический GIF. "
            "Файл будет проверен до сохранения."
        ),
        widget=forms.ClearableFileInput(
            attrs={
                "accept": "image/jpeg,image/png,image/webp,image/gif",
                "class": "form-control",
            }
        ),
    )

    confirm_automotive_content = forms.BooleanField(
        required=True,
        label=(
            "Подтверждаю, что на фото изображена автомобильная "
            "запчасть или инструмент, и разрешаю автоматическую проверку."
        ),
        error_messages={
            "required": (
                "Перед анализом подтвердите содержимое фотографии."
            )
        },
        widget=forms.CheckboxInput(
            attrs={"class": "form-check-input"}
        ),
    )
