"""
Кастомная миграция для создания суперпользователя, групп (ролей)
и автоматического назначения им всех необходимых прав доступа.

Эта миграция является идемпотентной: ее можно безопасно запускать
несколько раз, она не создаст дубликатов и всегда приведет
систему в ожидаемое состояние.
"""

from decouple import config

from django.db import migrations

# ==============================================================================
# КОНФИГУРАЦИЯ РОЛЕЙ И ПРАВ ДОСТУПА
# ==============================================================================

# Словарь ролей с правами доступа, которые должны быть созданы в системе.
# Ключ верхнего уровня: Название роли (Группы).
# Вложенный ключ: Имя приложения (app_label).
# Вложенное значение: Список кодовых имен прав (codename) для моделей этого приложения.

ROLES_PERMISSIONS = {
    'Оператор': {
        'leads': [
            'add_potentialclient',
            'change_potentialclient',
            'delete_potentialclient',
            'view_potentialclient',
        ],
    },
    'Маркетолог': {
        'products': [
            'add_service',
            'change_service',
            'delete_service',
            'view_service',
        ],
        'advertisements': [
            'add_adcampaign',
            'change_adcampaign',
            'delete_adcampaign',
            'view_adcampaign',
        ],
    },
    'Менеджер': {
        'leads': [
            'view_potentialclient',
        ],
        'contracts': [
            'add_contract',
            'change_contract',
            'delete_contract',
            'view_contract',
        ],
        'customers': [
            'add_activeclient',
            'change_activeclient',
            'delete_activeclient',
            'view_activeclient',
        ],
    },
    # Администратор получает все права через флаг is_superuser.
    # Создаем группу "Администратор" для единообразия и на случай,
    # если понадобится дать полный доступ обычному пользователю, не делая его суперюзером.
    'Администратор': {},
}


def ensure_permissions_exist(apps, schema_editor):
    """
    Вспомогательная функция для принудительного создания ContentType и Permission.

    **Проблема:**
    Стандартный механизм Django создает ContentType и Permission для моделей
    в рамках той же транзакции, что и создание таблиц. Кастомная миграция,
    запущенная в этой же транзакции, может не "увидеть" эти только что
    созданные объекты, что приводит к ошибкам на "чистой" базе данных.

    **Решение:**
    Эта функция решает проблему, явно создавая необходимые объекты ContentType
    и Permission, если они отсутствуют. Она является "идемпотентной", то есть
    безопасной для многократного запуска, благодаря использованию метода `get_or_create`.

    **Логика работы:**
    1. Динамически собирает список всех моделей, для которых нужно настроить права,
       из конфигурационной структуры `ROLES_PERMISSIONS`.
    2. Для каждой уникальной пары (приложение, модель) находит или создает
       соответствующий ей объект ContentType.
    3. Для каждого ContentType находит или создает 4 стандартных права
       ('add', 'change', 'delete', 'view').
    """
    # Получаем моделей, с которыми мы будем работать
    ContentType = apps.get_model('contenttypes', 'ContentType')
    Permission = apps.get_model('auth', 'Permission')

    # 1. Собираем информацию о всех моделях, упомянутых в ролях
    # Проходим по всей структуре `ROLES_PERMISSIONS` и собираем
    # уникальные пары (app_label, model_name), а также их "человеческие"
    # имена для создания красивых названий прав (e.g., "Can view услуга").
    models_info = {}

    for role_perms in ROLES_PERMISSIONS.values():
        for app_label, perm_codenames in role_perms.items():
            for perm_codename in perm_codenames:
                # Извлекаем имя модели из кодового имени права
                # Пример: 'view_service' -> 'service'
                model_name = perm_codename.split('_')[1]

                # Проверяем, не обработали ли мы уже эту модель
                if (app_label, model_name) not in models_info:

                    try:
                        # Получаем класс модели, чтобы извлечь ее метаданные
                        model = apps.get_model(app_label, model_name)
                        # Сохраняем "человеческое" имя, которое Django
                        # использует для названий прав (e.g., "услуга")
                        models_info[(app_label, model_name)] = model._meta.verbose_name
                    except LookupError:
                        # На случай, если в ROLES_PERMISSIONS опечатка
                        print(f"    - ПРЕДУПРЕЖДЕНИЕ: Модель {app_label}.{model_name} не найдена. Пропускаем.")
                        continue

    # 2. Создаем ContentType для каждой модели
    permissions_created_count = 0

    # Проходим по каждой найденной паре (приложение, модель)
    for (app_label, model_name), verbose_name in models_info.items():

        # Создаем или получаем ContentType
        content_type, created = ContentType.objects.get_or_create(
            app_label=app_label,
            model=model_name,
        )

        # 3. Создаем или получаем 4 стандартных права для этого ContentType
        for action in ['add', 'change', 'delete', 'view']:
            codename = f"{action}_{model_name}"
            name = f"Can {action} {verbose_name}"

            _, created = Permission.objects.get_or_create(
                codename=codename,
                name=name,
                content_type=content_type,
            )

            if created:
                permissions_created_count += 1

    print(f"\n  Проверено {len(models_info)} моделей. Создано {permissions_created_count} новых прав доступа.")


def create_superuser_and_roles(apps, schema_editor):
    """
    Создает суперпользователя и группы (роли) с правами доступа.
    """
    # 0. Гарантируем, что все права существуют.
    ensure_permissions_exist(apps, schema_editor)

    # 1. Получаем все необходимые модели.
    # Используем apps.get_model() для получения исторических версий моделей,
    # соответствующих моменту применения этой миграции.
    User = apps.get_model('users', 'User')
    Profile = apps.get_model('users', 'Profile')
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    # 2. Создаем суперпользователя
    # Используем decouple.config() для чтения из .env
    admin_username = config('ADMIN_USERNAME', default='admin')
    admin_password = config('ADMIN_PASSWORD', default='password')
    admin_email = config('ADMIN_EMAIL', default='admin@example.com')

    # Проверяем, не существует ли уже такой пользователь
    try:
        if not User.objects.filter(username=admin_username).exists():
            admin_user = User.objects.create_superuser(
                username=admin_username,
                email=admin_email,
                password=admin_password
            )

            # Сигналы не работают во время миграций, поэтому профиль суперпользователю создаем вручную.
            Profile.objects.create(user=admin_user, position='Администратор')

            print(f"\n  Суперпользователь '{admin_username}' и его профиль успешно созданы.")
        else:
            print(f"\n  Создание суперпользователя '{admin_username}' пропущено (уже существует).")

    except Exception as exc:
        print(f"\n  Произошла ошибка при создании суперпользователя: {exc}")

    # 3. Создаем роли и назначаем права
    for role_name, permissions_data in ROLES_PERMISSIONS.items():
        # Создаем группу или получаем, если она уже существует
        group, created = Group.objects.get_or_create(name=role_name)

        if created:
            print(f"  Группа '{role_name}' успешно создана.")
        else:
            print(f"  Группа '{role_name}' уже существует.")

        # Перед назначением прав очищаем все текущие права группы.
        # Это делает миграцию идемпотентной: при повторном запуске
        # удаленные из конфига права будут убраны из группы.
        group.permissions.clear()

        # Переменная для хранения найденных объектов прав.
        permissions_to_add = []

        # Цикл по приложениям ('products', 'leads', ...)
        for app_label, perm_codenames in permissions_data.items():
            # Цикл по правам ('add_service', 'change_service' ...)
            for perm_codename in perm_codenames:
                try:
                    # Извлекаем имя модели из кодового имени права.
                    # Пример: 'view_service' -> 'service'
                    model_name = perm_codename.split('_')[1]

                    # Находим ContentType, который связывает право с конкретной моделью.
                    content_type = ContentType.objects.get(app_label=app_label, model=model_name)

                    # Находим сам объект права в базе данных.
                    permission = Permission.objects.get(content_type=content_type, codename=perm_codename)

                    # Добавляем право в список найденных объектов прав.
                    permissions_to_add.append(permission)

                    print(f"    - Право '{perm_codename}' для '{app_label}.{model_name}' назначено.")

                except ContentType.DoesNotExist:
                    print(
                        f"    - ОШИБКА: Модель '{app_label}.{model_name}' не найдена для права '{perm_codename}'."
                    )
                except Permission.DoesNotExist:
                    print(f"    - ОШИБКА: Право '{perm_codename}' не найдено в базе данных.")
                except IndexError:
                    print(
                        f"    - ПРЕДУПРЕЖДЕНИЕ: Неверный формат кодового имени права '{perm_codename}'."
                        f"      Право пропущено."
                    )

        # Добавляем все найденные права в группу.
        if permissions_to_add:
            group.permissions.set(permissions_to_add)
            print(f"    -> Все найденные права успешно назначены группе '{role_name}'.")


def revert_migration(apps, schema_editor):
    """
    Откат миграции: удаляет созданные данные.
    """
    User = apps.get_model('users', 'User')
    Group = apps.get_model('auth', 'Group')

    # Удаление суперпользователя каскадно удалит и связанный с ним профиль
    admin_username = config('ADMIN_USERNAME', default='admin')
    User.objects.filter(username=admin_username).delete()

    # Удаляем группы
    Group.objects.filter(name__in=ROLES_PERMISSIONS.keys()).delete()

    print("\n  Суперпользователь и все созданные группы были удалены.")


class Migration(migrations.Migration):
    # Эта миграция должна выполняться только после того, как будут созданы
    # начальные таблицы для всех задействованных приложений.
    dependencies = [
        ('users', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),  # Стандартная миграция auth
        ('contenttypes', '0002_remove_content_type_name'),  # Стандартная миграция contenttypes
        ('products', '0001_initial'),
        ('advertisements', '0001_initial'),
        ('leads', '0001_initial'),
        ('contracts', '0001_initial'),
        ('customers', '0001_initial'),
    ]

    operations = [
        # `migrations.RunPython` выполняет кастомный Python-код.
        # `atomic=True` гарантирует, что все операции внутри функции будут выполнены в одной транзакции.
        migrations.RunPython(
            code=create_superuser_and_roles,
            reverse_code=revert_migration,
            atomic=True
        ),
    ]
