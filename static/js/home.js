document.addEventListener('DOMContentLoaded', function() {
    const slides = document.querySelectorAll('.slide');
    const indicators = document.querySelectorAll('.slide-indicator');
    const prevButton = document.querySelector('.prev-slide');
    const nextButton = document.querySelector('.next-slide');
    
    let currentSlide = 0;
    let slideInterval;
    const intervalTime = 5000; // 5 seconds between slides
    
    // Initialize the slideshow
    function initSlideshow() {
        if (slides.length === 0) return;
        
        // Set the first slide as active
        showSlide(0);
        
        // Start automatic slideshow
        startSlideshow();
        
        // Add event listeners
        if (prevButton) {
            prevButton.addEventListener('click', showPrevSlide);
        }
        
        if (nextButton) {
            nextButton.addEventListener('click', showNextSlide);
        }
        
        // Add indicator event listeners
        indicators.forEach((indicator, index) => {
            indicator.addEventListener('click', () => {
                showSlide(index);
            });
        });
        
        // Pause slideshow on hover
        const slideshow = document.querySelector('.venue-slideshow');
        if (slideshow) {
            slideshow.addEventListener('mouseenter', () => {
                clearInterval(slideInterval);
            });
            
            slideshow.addEventListener('mouseleave', () => {
                startSlideshow();
            });
        }
    }
    
    // Show a specific slide
    function showSlide(index) {
        if (slides.length === 0) return;
        
        // Hide all slides
        slides.forEach(slide => {
            slide.classList.remove('active');
        });
        
        // Update indicators
        if (indicators.length > 0) {
            indicators.forEach(indicator => {
                indicator.classList.remove('active');
            });
            indicators[index].classList.add('active');
        }
        
        // Show the selected slide
        slides[index].classList.add('active');
        currentSlide = index;
    }
    
    // Show the next slide
    function showNextSlide() {
        if (slides.length === 0) return;
        
        let nextIndex = currentSlide + 1;
        if (nextIndex >= slides.length) {
            nextIndex = 0;
        }
        showSlide(nextIndex);
    }
    
    // Show the previous slide
    function showPrevSlide() {
        if (slides.length === 0) return;
        
        let prevIndex = currentSlide - 1;
        if (prevIndex < 0) {
            prevIndex = slides.length - 1;
        }
        showSlide(prevIndex);
    }
    
    // Start automatic slideshow
    function startSlideshow() {
        clearInterval(slideInterval);
        slideInterval = setInterval(showNextSlide, intervalTime);
    }
    
    // Initialize the slideshow
    initSlideshow();
});
