document.addEventListener('DOMContentLoaded', function() {
    // Rating stars functionality
    const ratingContainer = document.querySelector('.rating-stars');
    const ratingInput = document.getElementById('rating-value');
    const ratingDisplay = document.getElementById('rating-display');
    
    if (ratingContainer && ratingInput) {
        const stars = ratingContainer.querySelectorAll('i');
        
        // Set initial rating if it exists
        if (ratingInput.value) {
            updateStars(ratingInput.value);
        }
        
        // Add click events to stars
        stars.forEach((star, index) => {
            star.addEventListener('click', () => {
                const rating = index + 1;
                ratingInput.value = rating;
                updateStars(rating);
                
                if (ratingDisplay) {
                    ratingDisplay.textContent = rating;
                }
            });
        });
        
        // Hover effects for stars
        stars.forEach((star, index) => {
            // Mouse enter - show rating preview
            star.addEventListener('mouseenter', () => {
                stars.forEach((s, i) => {
                    if (i <= index) {
                        s.classList.remove('far');
                        s.classList.add('fas');
                        s.classList.add('text-warning');
                    } else {
                        s.classList.remove('fas');
                        s.classList.remove('text-warning');
                        s.classList.add('far');
                    }
                });
            });
        });
        
        // Mouse leave - restore original rating
        ratingContainer.addEventListener('mouseleave', () => {
            updateStars(ratingInput.value || 0);
        });
        
        // Function to update stars based on rating
        function updateStars(rating) {
            stars.forEach((star, index) => {
                if (index < rating) {
                    star.classList.remove('far');
                    star.classList.add('fas');
                    star.classList.add('text-warning');
                } else {
                    star.classList.remove('fas');
                    star.classList.remove('text-warning');
                    star.classList.add('far');
                }
            });
        }
    }
});
