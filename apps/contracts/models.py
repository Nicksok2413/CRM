"""
Модели для приложения contracts (контракты).
"""

from decimal import Decimal
from typing import TYPE_CHECKING

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models
from django_clamd.validators import validate_file_infection

from apps.common.models import BaseModel
from apps.common.utils import create_dynamic_upload_path
from apps.common.validators import validate_document_size
from apps.products.models import Service

# Этот блок импортируется только во время статической проверки типов.
# Он предотвращает ошибки циклического импорта во время выполнения.
if TYPE_CHECKING:
    from apps.customers.models import ActiveClient


class Contract(BaseModel):
    """
    Модель для хранения информации о контрактах.
    """

    name = models.CharField(max_length=200, verbose_name="Название контракта")
    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,  # Запрещаем удалять услугу, если по ней есть контракты
        related_name="contracts",
        verbose_name="Предоставляемая услуга",
    )
    document = models.FileField(
        upload_to=create_dynamic_upload_path,
        blank=True,
        null=True,
        verbose_name="Файл с документом",
        validators=[
            # Разрешаем только определенные типы файлов.
            FileExtensionValidator(allowed_extensions=["pdf", "doc", "docx", "jpg", "jpeg", "png"]),
            # Валидатор размера файла.
            validate_document_size,
            # Антивирусный сканер.
            validate_file_infection,
        ],
    )
    amount = models.DecimalField(
        max_digits=12,
        db_index=True,  # Для ускорения операций фильтрации и сортировки
        decimal_places=2,
        verbose_name="Сумма",
        validators=[MinValueValidator(Decimal("0.00"))],  # Сумма не может быть отрицательной
    )
    start_date = models.DateField(db_index=True, verbose_name="Дата заключения")
    end_date = models.DateField(db_index=True, verbose_name="Дата окончания")

    # Явная аннотация для обратной связи.
    # PyCharm и mypy теперь знают, что у `Contract` есть
    # аттрибут `active_client`, который возвращает объект `ActiveClient`.
    # Так как связь OneToOne может отсутствовать, то может возвращать None.
    active_client: "ActiveClient | None"

    def clean(self) -> None:
        """
        Переопределяем метод clean для добавления кастомной логики валидации,
        которая затрагивает несколько полей.
        """
        # Вызываем родительский метод clean для выполнения стандартных валидаций
        super().clean()
        # Проверяем, что дата окончания не раньше даты начала
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError("Дата окончания контракта не может быть раньше даты его начала.")

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = "Контракт"
        verbose_name_plural = "Контракты"
        ordering = ["-start_date"]
