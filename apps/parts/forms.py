from django import forms


class PartImageAnalysisUploadForm(forms.Form):
    """Загрузка фотографии для автоматической проверки и распознавания."""

    MAX_IMAGE_BYTES = 5 * 1024 * 1024

    image = forms.ImageField(
        label="Фотография запчасти или инструмента",
        help_text=(
            "JPEG, PNG, WEBP или статический GIF. "
            "Максимальный размер — 5 МБ. "
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

    def clean_image(self):
        image = self.cleaned_data["image"]
        if int(getattr(image, "size", 0) or 0) > self.MAX_IMAGE_BYTES:
            raise forms.ValidationError(
                "Размер изображения не должен превышать 5 МБ."
            )
        return image
