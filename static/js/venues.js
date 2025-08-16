// Slideshow functionality
document.addEventListener('DOMContentLoaded', function() {
    // Set up click handlers for navigation buttons
    document.querySelectorAll('.slide-nav').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const venueId = this.dataset.venue;
            const direction = parseInt(this.dataset.direction);
            changeSlide(venueId, direction);
        });
    });

    // Set up click handlers for dots
    document.querySelectorAll('.dot').forEach(dot => {
        dot.addEventListener('click', function(e) {
            e.preventDefault();
            const venueId = this.dataset.venue;
            const index = parseInt(this.dataset.index);
            currentSlide(venueId, index);
        });
    });

    // Start automatic slideshow for all venues
    document.querySelectorAll('.venue-slideshow').forEach(slideshow => {
        const venueId = slideshow.id.split('-').pop();
        setInterval(() => changeSlide(venueId, 1), 5000); // Change slide every 5 seconds
    });
});

function changeSlide(venueId, direction) {
    const slideshow = document.getElementById(`venue-slideshow-${venueId}`);
    const slides = slideshow.getElementsByClassName('venue-slide');
    const dots = slideshow.getElementsByClassName('dot');
    
    // Find current slide
    let currentIndex = Array.from(slides).findIndex(slide => slide.classList.contains('active'));
    
    // Remove active class from current slide and dot
    slides[currentIndex].classList.remove('active');
    if (dots.length > 0) dots[currentIndex].classList.remove('active');
    
    // Calculate new index
    let newIndex = currentIndex + direction;
    if (newIndex >= slides.length) newIndex = 0;
    if (newIndex < 0) newIndex = slides.length - 1;
    
    // Add active class to new slide and dot
    slides[newIndex].classList.add('active');
    if (dots.length > 0) dots[newIndex].classList.add('active');
}

function currentSlide(venueId, index) {
    const slideshow = document.getElementById(`venue-slideshow-${venueId}`);
    const slides = slideshow.getElementsByClassName('venue-slide');
    const dots = slideshow.getElementsByClassName('dot');
    
    // Remove active class from all slides and dots
    Array.from(slides).forEach(slide => slide.classList.remove('active'));
    Array.from(dots).forEach(dot => dot.classList.remove('active'));
    
    // Add active class to selected slide and dot
    slides[index].classList.add('active');
    dots[index].classList.add('active');
}

// Pause slideshow on hover
document.querySelectorAll('.venue-slideshow').forEach(slideshow => {
    let intervalId;
    const venueId = slideshow.id.split('-').pop();
    
    slideshow.addEventListener('mouseenter', () => {
        clearInterval(intervalId);
    });
    
    slideshow.addEventListener('mouseleave', () => {
        intervalId = setInterval(() => changeSlide(venueId, 1), 5000);
    });
});
