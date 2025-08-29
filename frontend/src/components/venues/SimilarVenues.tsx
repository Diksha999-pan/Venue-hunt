import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Card, Row, Col, Alert, Spinner } from 'react-bootstrap';
import { Link } from 'react-router-dom';

interface Venue {
  id: number;
  name: string;
  description: string;
  address: string;
  city: string;
  capacity: number;
  price_per_person: number;
  has_parking: boolean;
  has_wifi: boolean;
  has_sound_system: boolean;
  has_catering: boolean;
  average_rating: number;
  similarity_score?: number;
  images: { image: string }[];
}

interface SimilarVenuesProps {
  venueId: number;
}

const SimilarVenues: React.FC<SimilarVenuesProps> = ({ venueId }) => {
  const [similarVenues, setSimilarVenues] = useState<Venue[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSimilarVenues = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        const response = await axios.get<Venue[]>(
          `/api/recommendations/venues/${venueId}/similar/`
        );
        
        setSimilarVenues(response.data);
      } catch (err) {
        setError('Failed to load similar venues. Please try again later.');
        console.error('Error fetching similar venues:', err);
      } finally {
        setIsLoading(false);
      }
    };

    if (venueId) {
      fetchSimilarVenues();
    }
  }, [venueId]);

  if (isLoading) {
    return (
      <div className="text-center my-4">
        <Spinner animation="border" variant="primary" />
      </div>
    );
  }

  if (error) {
    return <Alert variant="danger">{error}</Alert>;
  }

  if (!similarVenues.length) {
    return null;
  }

  return (
    <div className="similar-venues-section my-4">
      <h3 className="mb-4">Similar Venues You May Like</h3>
      <Row xs={1} md={3} className="g-4">
        {similarVenues.map((venue) => (
          <Col key={venue.id}>
            <Card className="h-100 venue-card">
              {venue.images?.[0] && (
                <Card.Img
                  variant="top"
                  src={venue.images[0].image}
                  alt={venue.name}
                  className="venue-image"
                />
              )}
              <Card.Body>
                <Card.Title>{venue.name}</Card.Title>
                <Card.Text className="text-muted mb-2">
                  <i className="fas fa-map-marker-alt"></i> {venue.city}
                </Card.Text>
                <Card.Text className="venue-description">
                  {venue.description.substring(0, 100)}...
                </Card.Text>
                <div className="venue-details">
                  <div className="detail-item">
                    <i className="fas fa-users"></i>
                    <span>Up to {venue.capacity} people</span>
                  </div>
                  <div className="detail-item">
                    <i className="fas fa-rupee-sign"></i>
                    <span>₹{venue.price_per_person}/person</span>
                  </div>
                </div>
                <div className="venue-amenities">
                  {venue.has_parking && (
                    <span className="amenity-badge">
                      <i className="fas fa-parking"></i> Parking
                    </span>
                  )}
                  {venue.has_wifi && (
                    <span className="amenity-badge">
                      <i className="fas fa-wifi"></i> Wi-Fi
                    </span>
                  )}
                  {venue.has_sound_system && (
                    <span className="amenity-badge">
                      <i className="fas fa-music"></i> Sound
                    </span>
                  )}
                  {venue.has_catering && (
                    <span className="amenity-badge">
                      <i className="fas fa-utensils"></i> Catering
                    </span>
                  )}
                </div>
              </Card.Body>
              <Card.Footer className="bg-transparent border-top-0">
                <Link
                  to={`/venues/${venue.id}`}
                  className="btn btn-outline-primary w-100"
                >
                  View Details
                </Link>
              </Card.Footer>
              {venue.similarity_score && (
                <div className="similarity-score">
                  {Math.round(venue.similarity_score * 100)}% match
                </div>
              )}
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
};

export default SimilarVenues;