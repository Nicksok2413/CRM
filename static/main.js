// Этот код будет выполнен, когда вся HTML-страница будет загружена
document.addEventListener("DOMContentLoaded", function() {

  // Инициализация Flatpickr для всех элементов с классом 'datepicker'
  flatpickr(".datepicker", {
    // Устанавливаем русскую локализацию
    "locale": "ru",

    // altInput: true
    // Создает дополнительное, видимое для пользователя поле ввода.
    // Оригинальное поле <input> становится скрытым и хранит дату в "машинном" формате.
    "altInput": true,

    // altFormat: "d-m-Y"
    // Формат даты для видимого поля (то, что видит пользователь).
    "altFormat": "d-m-Y",

    // dateFormat: "Y-m-d"
    // Формат даты для оригинального, скрытого поля.
    // Это тот формат, который будет отправлен на сервер.
    // Он соответствует стандарту Django.
    "dateFormat": "Y-m-d",

    // Позволяет пользователю вводить дату вручную в том же формате
    "allowInput": true,
  });

  // ================== ЛОГИКА ДЛЯ ГРАФИКА ==================

  // Находим элемент canvas на странице
  const chartCanvas = document.getElementById('leadsChart');

  // Проверяем, существует ли этот элемент на текущей странице
  // (чтобы код не падал на других страницах)
  if (chartCanvas) {

    // Асинхронно запрашиваем данные с нашего API-endpoint
    fetch('/leads/api/lead-stats/')
      .then(response => response.json())
      .then(data => {

        // Получаем контекст для рисования
        const ctx = chartCanvas.getContext('2d');

        // Создаем новый график с помощью Chart.js
        new Chart(ctx, {
          type: 'line', // Тип графика: линейный
          data: {
            labels: data.labels, // Метки по оси X (даты)
            datasets: [{
              label: 'Количество новых лидов',
              data: data.data, // Данные по оси Y (количества)
              borderColor: 'rgb(75, 192, 192)', // Цвет границ
              backgroundColor: 'rgba(75, 192, 192, 0.2)', // Цвет заливки под линией
              fill: true, // Включаем заливку
              tension: 0.4, // Делает линию плавной (кубической)
              pointBackgroundColor: 'rgb(75, 192, 192)', // Цвет точек
              pointRadius: 4, // Размер точек
            }]
          },
          options: {
            // === НАСТРОЙКА ОСЕЙ ===
            scales: {
              y: {
                beginAtZero: true,
                title: { // Заголовок для оси Y
                  display: true,
                  text: 'Количество лидов'
                }
              },
              x: {
                title: { // Заголовок для оси X
                  display: true,
                  text: 'Дата'
                }
              }
            },
            // === ОТКЛЮЧАЕМ ЛИШНЕЕ ===
            maintainAspectRatio: false // Позволяет графику лучше вписываться в контейнер
          }
        });
      })
      .catch(error => console.error('Error fetching chart data:', error));
  }
  // ========================================================

});