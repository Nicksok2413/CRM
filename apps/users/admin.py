"""
Настройки административной панели для приложения users.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Profile, User


class ProfileInline(admin.StackedInline):
    """
    Класс для встраивания модели Profile в административную панель User.

    admin.StackedInline отображает поля связанной модели в столбик,
    что удобно для моделей с несколькими полями (в отличие от TabularInline).
    """

    # Указываем модель, которую нужно встроить.
    model = Profile

    # Указываем что у одного пользователя может быть только один профиль.
    max_num = 1

    # Запрещаем удаление профиля отдельно от пользователя.
    can_delete = False

    # Заголовок, который будет отображаться над полями профиля.
    # Используем единственное число, так как профиль у пользователя один.
    verbose_name_plural = "Профиль сотрудника"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Административный класс для модели User.
    Переопределяет и расширяет стандартный класс UserAdmin.

    Наследуем от BaseUserAdmin, чтобы сохранить всю встроенную функциональность Django:
    формы смены пароля, управление правами и группами и т.д.
    """

    # Добавляем ProfileInline в список "встраиваемых" элементов.
    inlines = (ProfileInline,)

    # Копируем fieldsets из BaseUserAdmin и добавляем 'patronymic' в секцию 'Personal info'.
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "patronymic", "email")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """
    Административный класс для модели Profile.

    Profile будет редактироваться через User,
    но для просмотра списка всех профилей и для отладки регистрируем.
    """

    # Поля для отображения в списке всех профилей.
    list_display = ("user", "position")

    # Поля, по которым будет работать поиск.
    search_fields = ("user__username", "user__first_name", "user__last_name", "position")

    # Оптимизация запросов: при загрузке списка профилей
    # сразу загружаем связанные данные пользователя одним SQL-запросом, избегая проблемы "N+1".
    # `list_select_related` заставляет Django использовать SQL JOIN, получая все данные за один запрос.
    list_select_related = ("user",)
