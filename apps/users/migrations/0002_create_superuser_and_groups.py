"""
Кастомная миграция для создания суперпользователя и групп (ролей).
"""

from decouple import config

from django.db import migrations, transaction

# Список ролей, которые должны быть созданы в системе.
# Это позволяет легко добавлять новые роли в будущем.
ROLES = ['Администратор', 'Оператор', 'Маркетолог', 'Менеджер']


def create_superuser_and_groups(apps, schema_editor):
    """
    Создает суперпользователя и основные группы пользователей (роли).
    """
    # =========================================================================
    # 1. Создание суперпользователя
    # =========================================================================

    # Получаем модели User и Profile, актуальные для данной миграции.
    User = apps.get_model('users', 'User')
    Profile = apps.get_model('users', 'Profile')

    # Используем decouple.config() для чтения из .env
    admin_username = config('ADMIN_USERNAME', default='admin')
    admin_password = config('ADMIN_PASSWORD', default='password')
    admin_email = config('ADMIN_EMAIL', default='admin@example.com')

    # Проверяем, не существует ли уже такой пользователь
    try:
        with transaction.atomic():
            if not User.objects.filter(username=admin_username).exists():
                # Создаем суперпользователя
                admin_user = User.objects.create_superuser(
                    username=admin_username,
                    email=admin_email,
                    password=admin_password
                )

                # Создаем профиль суперпользователю, потому что сигнал не сработает
                Profile.objects.create(user=admin_user, position='Администратор')

                print(f"\n  Суперпользователь '{admin_username}' и его профиль успешно созданы.")
            else:
                print(f"\n  Создание суперпользователя '{admin_username}' пропущено (уже существует).")

    except Exception as exc:
        print(f"\n  Произошла ошибка при создании суперпользователя: {exc}")


    # =========================================================================
    # 2. Создание групп (ролей)
    # =========================================================================

    # Получаем модель Group
    Group = apps.get_model('auth', 'Group')

    for role_name in ROLES:
        # get_or_create пытается найти группу с таким именем.
        # Если находит - возвращает ее. Если нет - создает новую.
        group, created = Group.objects.get_or_create(name=role_name)
        if created:
            print(f"  Группа '{role_name}' успешно создана.")
        else:
            print(f"  Группа '{role_name}' уже существует.")


def remove_superuser_and_groups(apps, schema_editor):
    """
    Откат миграции: удаляет созданные данные.
    """
    User = apps.get_model('users', 'User')
    Group = apps.get_model('auth', 'Group')

    # Удаление суперпользователя каскадно удалит и связанный с ним профиль
    admin_username = config('ADMIN_USERNAME', default='admin')
    deleted_users_count, _ = User.objects.filter(username=admin_username).delete()

    if deleted_users_count > 0:
        print(f"  Суперпользователь '{admin_username}' удален.")

    # Удаляем группы
    deleted_groups_count, _ = Group.objects.filter(name__in=ROLES).delete()

    if deleted_groups_count > 0:
        print(f"  Группы {ROLES} удалены.")


class Migration(migrations.Migration):

    # Эта миграция должна выполняться после создания начальных таблиц User и Group.
    # Указываем зависимость от последней миграции приложения users и auth.
    dependencies = [
        ('users', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'), # Стандартная миграция auth
    ]

    operations = [
        # `migrations.RunPython` выполняет кастомный Python-код.
        migrations.RunPython(create_superuser_and_groups, reverse_code=remove_superuser_and_groups),
    ]