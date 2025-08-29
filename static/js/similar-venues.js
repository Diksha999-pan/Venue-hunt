// Function to create a venue card element
function createVenueCard(venue) {
    const col = document.createElement('div');
    col.className = 'col-lg-2 col-md-3 col-sm-4 col-6 mb-3';
    
    // Ensure the image URL is properly constructed
    let imageUrl = venue.primary_image || '/static/images/default-venue.jpg';
    if (imageUrl && !imageUrl.startsWith('http') && !imageUrl.startsWith('/')) {
        imageUrl = '/' + imageUrl;
    }

    const description = venue.description ? venue.description.substring(0, 100) + '...' : '';
    const rating = venue.average_rating ? 
        '<div class="venue-rating">' +
            '<i class="fas fa-star text-warning"></i> ' + 
            parseFloat(venue.average_rating).toFixed(1) +
        '</div>' : '';
    
    const matchBadge = venue.similarity_score ?
        '<div class="position-absolute top-0 end-0 m-2">' +
            '<span class="badge bg-primary">' +
                Math.round(venue.similarity_score * 100) + '% Match' +
            '</span>' +
        '</div>' : '';
    
    const card = document.createElement('div');
    card.className = 'card h-100';
    
    const cardHtml = [
        '<img',
        ' src="' + imageUrl + '"',
        ' class="card-img-top"',
        ' alt="' + venue.name + '"',
        ' style="height: 140px; object-fit: cover;">',,
        matchBadge,
        '<div class="card-body">',
        '<h5 class="card-title">' + venue.name + '</h5>',
        '<p class="card-text text-muted">',
        '<i class="fas fa-map-marker-alt"></i> ' + venue.address,
        '</p>',
        '<p class="card-text">' + description + '</p>',
        '<div class="venue-details mb-3">',
        '<div><i class="fas fa-users"></i> Up to ' + venue.capacity + ' people</div>',
        '<div><i class="fas fa-rupee-sign"></i> ₹' + venue.price_per_person + '/person</div>',
        rating,
        '</div>',
        '<a href="/venues/' + venue.id + '/" class="btn btn-outline-primary w-100" onclick="window.location.href=\'/venues/' + venue.id + '/\'; return false;">View Details</a>',
        '</div>'
    ].join('');

    card.innerHTML = cardHtml;
    col.appendChild(card);
    return col;
}

// Function to load similar venues
function loadSimilarVenues(venueId) {
    const container = document.getElementById('similarVenues');
    if (!container) {
        console.error('Similar venues container not found');
        return;
    }
    
    // Show loading state
    container.innerHTML = 
        '<div class="col-12 text-center">' +
            '<div class="spinner-border text-primary" role="status">' +
                '<span class="visually-hidden">Loading similar venues...</span>' +
            '</div>' +
            '<p class="mt-2">Finding similar venues...</p>' +
        '</div>';

    // Log request details
    console.log('Fetching similar venues for venue ID:', venueId);

    // Fetch similar venues
    // Get CSRF token from cookie
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    fetch('/api/recommendations/venues/' + venueId + '/similar/?format=json', {
        method: 'GET',
        headers: {
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCookie('csrftoken')
        },
        credentials: 'same-origin'
    })
        .then(response => {
            console.log('Response status:', response.status);
            if (!response.ok) {
                throw new Error(response.statusText || 'HTTP error! status: ' + response.status);
            }
            return response.json();
        })
        .then(data => {
            // Clear loading spinner
            container.innerHTML = '';

            if (!data || data.length === 0) {
                container.innerHTML = 
                    '<div class="col-12">' +
                        '<div class="alert alert-info text-center">' +
                            'No similar venues found at the moment.' +
                        '</div>' +
                    '</div>';
                return;
            }

            const row = document.createElement('div');
            row.className = 'row';
            
            // Create and append venue cards
            data.forEach(venue => {
                const venueCard = createVenueCard(venue);
                row.appendChild(venueCard);
            });

            container.appendChild(row);
        })
        .catch(error => {
            console.error('Error fetching similar venues:', error);
            container.innerHTML = 
                '<div class="col-12">' +
                    '<div class="alert alert-danger text-center">' +
                        '<strong>Error:</strong> Failed to load similar venues. Please try again later.' +
                    '</div>' +
                    '<div class="text-center mt-3">' +
                        '<button class="btn btn-outline-primary" onclick="loadSimilarVenues(' + venueId + ')">' +
                            '<i class="fas fa-sync-alt"></i> Try Again' +
                        '</button>' +
                    '</div>' +
                '</div>';
        });
}