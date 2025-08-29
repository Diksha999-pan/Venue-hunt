document.addEventListener('DOMContentLoaded', function() {
    // Get all download receipt buttons
    const downloadButtons = document.querySelectorAll('a[href*="download_receipt"]');
    
    // Add click event listener to each download button
    downloadButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            // Get the loader element
            const spinner = document.querySelector('.loading-spinner');
            
            // Make sure the button has the data-no-loader attribute
            if (!this.hasAttribute('data-no-loader')) {
                this.setAttribute('data-no-loader', 'true');
            }
            
            // Hide the loader that may have been activated
            setTimeout(() => {
                spinner.classList.remove('active');
            }, 1000); // Short delay to ensure download has started
        });
    });
});
