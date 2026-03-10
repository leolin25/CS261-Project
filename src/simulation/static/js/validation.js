document.addEventListener("DOMContentLoaded", function() {
    const configForm = document.getElementById('config-form');
    const errorContainer = document.getElementById('error-message');

    configForm.addEventListener('submit', function(event) {
        // Clear previous errors
        errorContainer.style.display = 'none';
        errorContainer.textContent = '';
        
        let errorMsg = '';

        // Get field values
        const inboundFlow = parseInt(document.getElementById('inbound_flow').value);
        const outboundFlow = parseInt(document.getElementById('outbound_flow').value);
        const numRunways_mixed = parseInt(document.getElementById('num_runways_mixed').value);
        const numRunways_to = parseInt(document.getElementById('num_runways_to').value);
        const numRunways_la = parseInt(document.getElementById('num_runways_la').value);
        const max_wait = parseInt(document.getElementById('max_wait').value);


        //Protection against negative flows
        if (inboundFlow < 0 || outboundFlow < 0) {
            errorMsg = "Error: Flight flow rates per hour cannot be negative values.";
        }
        
        // Limit the number of runways (1-10)
        else if ((numRunways_mixed + numRunways_to + numRunways_la) < 1 || (numRunways_mixed + numRunways_to + numRunways_la) > 10) {
            errorMsg = "Error: The number of operational runways must be strictly between 1 and 10.";
        }

        else if (max_wait < 0){
            errorMsg = "Error: Flight must not have a negative max wait time";

        }

        // If an error exists, prevent form submission and display the message
        if (errorMsg !== '') {
            event.preventDefault(); 
            errorContainer.textContent = errorMsg;
            errorContainer.style.display = 'block';
            
            errorContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    });
});