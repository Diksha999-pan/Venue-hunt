document.addEventListener('DOMContentLoaded', function() {
    // Get the category and events select elements
    const categorySelect = document.getElementById('id_event_category');
    const eventsSelect = document.getElementById('id_event_type');
    
    if (categorySelect && eventsSelect) {
        // Define event types by category
        const eventTypesByCategory = {
            'formal': [
                'conference', 'business_meeting', 'product_launch', 
                'seminar_workshop', 'award_ceremony'
            ],
            'informal': [
                'birthday_party', 'casual_gathering', 'wedding', 
                'engagement', 'games_night', 'anniversary'
            ]
        };
        
        // Store all options for later use
        const allOptions = Array.from(eventsSelect.options);
        
        // Function to filter options by category
        function filterEventOptions(category) {
            // Clear current options
            eventsSelect.innerHTML = '';
            
            // Add "Other" option first
            const otherOption = allOptions.find(opt => opt.value === 'other');
            if (otherOption) {
                eventsSelect.appendChild(otherOption.cloneNode(true));
            }
            
            // Add options for the selected category
            const categoryEvents = eventTypesByCategory[category] || [];
            allOptions.forEach(option => {
                if (categoryEvents.includes(option.value)) {
                    eventsSelect.appendChild(option.cloneNode(true));
                }
            });
            
            // If no options found, add all options
            if (eventsSelect.options.length <= 1) {
                allOptions.forEach(option => {
                    eventsSelect.appendChild(option.cloneNode(true));
                });
            }
        }
        
        // Initial filtering based on selected category
        filterEventOptions(categorySelect.value);
        
        // Add event listener for category changes
        categorySelect.addEventListener('change', function() {
            filterEventOptions(this.value);
        });
    }
});
