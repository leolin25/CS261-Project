document.addEventListener("DOMContentLoaded", function() {
    const configForm = document.getElementById('config-form');
    const errorContainer = document.getElementById('error-message');
    const errorTextSpan = document.getElementById('error-text');

    configForm.addEventListener('submit', function(event) {
        // Reset error state
        errorContainer.style.display = 'none';
        errorTextSpan.textContent = '';
        
        let errorMsg = '';

        // Get values
        // Use || 0 to treat empty fields as 0 for validation
        const inboundFlow = parseInt(document.getElementById('inbound_flow').value) || 0;
        const outboundFlow = parseInt(document.getElementById('outbound_flow').value) || 0;
        const numRunways = parseInt(document.getElementById('num_runways').value) || 0;

        // --- Validation ---

        // Rule 1: Negative values
        if (inboundFlow < 0 || outboundFlow < 0) {
            errorMsg = "Flight flow rates cannot be negative.";
        }
        
        // Rule 2: Number of runways out of 1-10 range
        else if (numRunways < 1 || numRunways > 10) {
            errorMsg = "Number of runways must be strictly between 1 and 10.";
        }

        // --- If there is an error ---
        if (errorMsg !== '') {
            event.preventDefault(); // Stop submission
            
            errorTextSpan.textContent = errorMsg; // Insert text
            errorContainer.style.display = 'flex'; // Show container (flex for alignment with icon)
            
            // Smooth scroll to the error if the form is long
            errorContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    });
});