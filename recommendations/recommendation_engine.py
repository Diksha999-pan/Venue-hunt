from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from venues.models import Venue
from .models import VenueSimilarityCache
from django.utils import timezone
from datetime import timedelta
import pandas as pd

class VenueRecommender:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=5000,  # Limit features to improve efficiency
            ngram_range=(1, 2)  # Include both unigrams and bigrams
        )
        self.similarity_matrix = None
        self.venue_indices = {}
        self.last_update = None
        self.update_interval = timedelta(hours=24)  # Update similarities daily

    def _prepare_venue_text(self, venue):
        """Combine venue features into a single text string for TF-IDF"""
        features = [
            venue.name,
            venue.description or "",
            venue.address or "",
            str(venue.capacity),
            str(venue.price_per_person),
            venue.get_event_category_display(),
            venue.get_supported_events_display(),
        ]
        
        # Add event category
        if hasattr(venue, 'get_event_category_display'):
            features.append(venue.get_event_category_display())
            
        # Add amenities
        if venue.has_parking:
            features.append("parking")
        if venue.has_wifi:
            features.append("wifi")
        if venue.has_sound_system:
            features.append("sound system")
        if venue.has_catering:
            features.append("catering")
        
        # Add supported events if available
        if hasattr(venue, 'get_supported_events_display'):
            features.append(venue.get_supported_events_display())
            
        # Filter out None values and join with spaces
        return ' '.join(str(f).lower() for f in features if f is not None)

    def _should_update_similarities(self):
        """Check if similarity matrix needs updating"""
        if not self.last_update:
            return True
        return timezone.now() - self.last_update > self.update_interval

    def update_similarity_matrix(self, force=False):
        """Update venue similarity matrix if needed"""
        if not force and not self._should_update_similarities():
            return

        # Get all venues and prepare text data
        venues = Venue.objects.all()
        venue_texts = []
        self.venue_indices = {}
        
        for idx, venue in enumerate(venues):
            self.venue_indices[venue.id] = idx
            venue_texts.append(self._prepare_venue_text(venue))
            
        # Calculate TF-IDF matrix
        tfidf_matrix = self.vectorizer.fit_transform(venue_texts)
        
        # Calculate similarity matrix
        self.similarity_matrix = cosine_similarity(tfidf_matrix)
        
        # Update cache in batches
        self._update_similarity_cache(venues)
        
        self.last_update = timezone.now()

    def _cache_similarity_scores(self, source_venue_id, similar_venues, similarity_scores):
        """Cache similarity scores for faster retrieval"""
        try:
            # Clear existing cache for this venue
            VenueSimilarityCache.objects.filter(source_venue_id=source_venue_id).delete()
            
            # Create new cache entries
            cache_entries = []
            source_venue = Venue.objects.get(id=source_venue_id)
            
            for venue, score in zip(similar_venues, similarity_scores):
                if score > 0:  # Only cache meaningful similarities
                    cache_entries.append(
                        VenueSimilarityCache(
                            source_venue=source_venue,
                            target_venue=venue,
                            similarity_score=score
                        )
                    )
            
            if cache_entries:
                VenueSimilarityCache.objects.bulk_create(
                    cache_entries,
                    ignore_conflicts=True,
                    batch_size=100
                )
                print(f"Cached {len(cache_entries)} similarity scores for venue {source_venue_id}")
            else:
                print("No significant similarities to cache")
                
        except Exception as e:
            print(f"Error caching similarity scores: {str(e)}")
            # Continue even if caching fails

    def _update_similarity_cache(self, venues, batch_size=1000):
        """Update similarity cache in database"""
        cache_entries = []
        
        for idx1, venue1 in enumerate(venues):
            similarities = []
            for idx2, venue2 in enumerate(venues):
                if idx1 != idx2:
                    similarities.append(
                        VenueSimilarityCache(
                            source_venue=venue1,
                            target_venue=venue2,
                            similarity_score=float(self.similarity_matrix[idx1][idx2])
                        )
                    )
                    
                # Create in batches to avoid memory issues
                if len(similarities) >= batch_size:
                    VenueSimilarityCache.objects.bulk_create(
                        similarities,
                        ignore_conflicts=True,
                        batch_size=batch_size
                    )
                    similarities = []
                    
            if similarities:  # Create remaining entries
                VenueSimilarityCache.objects.bulk_create(
                    similarities,
                    ignore_conflicts=True,
                    batch_size=batch_size
                )

    def get_similar_venues(self, venue_id, n=5):
        """Get n most similar venues to the given venue"""
        try:
            print(f"Finding similar venues for venue_id: {venue_id}")
            
            # Try to get from cache first
            similar_venues = (VenueSimilarityCache.objects
                .filter(source_venue_id=venue_id)
                .select_related('target_venue')
                .order_by('-similarity_score')[:n])
            
            if similar_venues.exists():
                print("Found similar venues in cache")
                return [v.target_venue for v in similar_venues]
            
            print("No cached recommendations found, computing new ones...")
            
            # Get all venues and prepare text data for TF-IDF
            venues = list(Venue.objects.all())
            venue_texts = []
            self.venue_indices = {}
            
            # Create text content for each venue
            for idx, venue in enumerate(venues):
                self.venue_indices[venue.id] = idx
                venue_text = self._prepare_venue_text(venue)
                venue_texts.append(venue_text)
                print(f"Prepared text for venue {venue.id}: {venue_text[:100]}...")
            
            # Calculate TF-IDF matrix
            if len(venue_texts) < 2:
                print("Not enough venues for meaningful recommendations")
                return []
                
            tfidf_matrix = self.vectorizer.fit_transform(venue_texts)
            print("Computed TF-IDF matrix")
            
            # Calculate similarity scores
            venue_idx = self.venue_indices[venue_id]
            venue_vector = tfidf_matrix[venue_idx]
            
            # Calculate cosine similarity between this venue and all others
            similarities = cosine_similarity(venue_vector, tfidf_matrix).flatten()
            print("Computed cosine similarities")
            
            # Get indices of top N similar venues (excluding self)
            similar_indices = np.argsort(similarities)[::-1][1:n+1]  # Exclude self (highest similarity)
            print(f"Found similar venue indices: {similar_indices}")
            
            # Get venue IDs from indices
            venue_ids = []
            similarity_scores = []
            for idx in similar_indices:
                for vid, vix in self.venue_indices.items():
                    if vix == idx:
                        venue_ids.append(vid)
                        similarity_scores.append(float(similarities[idx]))
            
            print(f"Found similar venue IDs: {venue_ids}")
            
            # Get similar venues
            similar_venues = list(Venue.objects.filter(id__in=venue_ids))
            print(f"Retrieved {len(similar_venues)} similar venues")
            
            # Sort venues by similarity score
            similar_venues.sort(key=lambda v: similarity_scores[venue_ids.index(v.id)], reverse=True)
            
            # Cache the results
            self._cache_similarity_scores(venue_id, similar_venues, similarity_scores)
            
            return similar_venues
            
        except (KeyError, IndexError):
            return Venue.objects.none()

    def get_personalized_recommendations(self, user, n=5):
        """Get personalized recommendations based on user's interaction history"""
        from .models import UserVenueInteraction
        
        # Get user's recent interactions
        recent_interactions = (UserVenueInteraction.objects
            .filter(user=user)
            .select_related('venue')
            .order_by('-timestamp')[:10])
        
        if not recent_interactions:
            # Return popular venues if no interaction history
            return Venue.objects.order_by('-average_rating')[:n]
        
        # Get similar venues for each interacted venue
        similar_venues = []
        weights = {
            'book': 3.0,  # Highest weight for bookings
            'favorite': 2.0,  # Medium weight for favorites
            'view': 1.0  # Lowest weight for views
        }
        
        for interaction in recent_interactions:
            similar = self.get_similar_venues(interaction.venue.id, n=3)
            weight = weights.get(interaction.interaction_type, 1.0)
            
            for venue in similar:
                similar_venues.append({
                    'venue': venue,
                    'score': weight * interaction.timestamp.timestamp()
                })
        
        # Aggregate and sort recommendations
        df = pd.DataFrame(similar_venues)
        if not df.empty:
            top_venues = (df.groupby('venue')['score']
                         .sum()
                         .sort_values(ascending=False)
                         .index[:n])
            return top_venues
        
        return Venue.objects.none()