document.addEventListener("DOMContentLoaded", function() {
    const configForm = document.getElementById('config-form');
    const errorContainer = document.getElementById('error-message');

    configForm.addEventListener('submit', function(event) {
        // Очищаем предыдущие ошибки
        errorContainer.style.display = 'none';
        errorContainer.textContent = '';
        
        let errorMsg = '';

        // Получаем значения полей
        const inboundFlow = parseInt(document.getElementById('inbound_flow').value);
        const outboundFlow = parseInt(document.getElementById('outbound_flow').value);
        const numRunways = parseInt(document.getElementById('num_runways').value);

        // Правило 1: Защита от отрицательных потоков (Security/Robustness requirement)
        if (inboundFlow < 0 || outboundFlow < 0) {
            errorMsg = "Error: Flight flow rates per hour cannot be negative values.";
        }
        
        // Правило 2: Ограничение количества полос (1-10)
        else if (numRunways < 1 || numRunways > 10) {
            errorMsg = "Error: The number of operational runways must be strictly between 1 and 10.";
        }

        // Если есть ошибка, останавливаем отправку формы и показываем сообщение
        if (errorMsg !== '') {
            event.preventDefault(); // Блокирует submit
            errorContainer.textContent = errorMsg;
            errorContainer.style.display = 'block';
            
            // Прокручиваем к сообщению об ошибке для удобства пользователя
            errorContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    });
});