import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { Container, Row, Col, Alert, Spinner } from 'react-bootstrap';
import SimilarVenues from './SimilarVenues';
import './VenueDetail.css';

interface VenueDetailParams {
  id: string;
}

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
  images: { image: string }[];
}

const VenueDetail: React.FC = () => {
  const { id } = useParams<VenueDetailParams>();
  const [venue, setVenue] = useState<Venue | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchVenueDetails = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        const response = await axios.get<Venue>(`/api/venues/${id}/`);
        setVenue(response.data);
      } catch (err) {
        setError('Failed to load venue details. Please try again later.');
        console.error('Error fetching venue details:', err);
      } finally {
        setIsLoading(false);
      }
    };

    if (id) {
      fetchVenueDetails();
    }
  }, [id]);

  if (isLoading) {
    return (
      <Container className="py-5">
        <div className="text-center">
          <Spinner animation="border" variant="primary" />
        </div>
      </Container>
    );
  }

  if (error) {
    return (
      <Container className="py-5">
        <Alert variant="danger">{error}</Alert>
      </Container>
    );
  }

  if (!venue) {
    return (
      <Container className="py-5">
        <Alert variant="warning">Venue not found</Alert>
      </Container>
    );
  }

  return (
    <Container className="py-5">
      <Row className="mb-4">
        <Col>
          <h1 className="venue-title">{venue.name}</h1>
          <p className="venue-location">
            <i className="fas fa-map-marker-alt"></i> {venue.address}, {venue.city}
          </p>
        </Col>
      </Row>

      {/* Venue Images */}
      <Row className="mb-4">
        <Col>
          <div className="venue-images">
            {venue.images.map((image, index) => (
              <img
                key={index}
                src={image.image}
                alt={`${venue.name} - Photo ${index + 1}`}
                className="venue-detail-image"
              />
            ))}
          </div>
        </Col>
      </Row>

      {/* Venue Details */}
      <Row className="mb-4">
        <Col md={8}>
          <div className="venue-description">
            <h2>About this Venue</h2>
            <p>{venue.description}</p>
          </div>
          
          <div className="venue-amenities mt-4">
            <h2>Amenities</h2>
            <div className="amenities-grid">
              {venue.has_parking && (
                <div className="amenity-item">
                  <i className="fas fa-parking"></i>
                  <span>Parking Available</span>
                </div>
              )}
              {venue.has_wifi && (
                <div className="amenity-item">
                  <i className="fas fa-wifi"></i>
                  <span>Free Wi-Fi</span>
                </div>
              )}
              {venue.has_sound_system && (
                <div className="amenity-item">
                  <i className="fas fa-music"></i>
                  <span>Sound System</span>
                </div>
              )}
              {venue.has_catering && (
                <div className="amenity-item">
                  <i className="fas fa-utensils"></i>
                  <span>Catering Services</span>
                </div>
              )}
            </div>
          </div>
        </Col>

        <Col md={4}>
          <div className="venue-quick-info">
            <div className="info-item">
              <i className="fas fa-users"></i>
              <div>
                <h3>Capacity</h3>
                <p>Up to {venue.capacity} people</p>
              </div>
            </div>
            <div className="info-item">
              <i className="fas fa-rupee-sign"></i>
              <div>
                <h3>Price</h3>
                <p>₹{venue.price_per_person} per person</p>
              </div>
            </div>
            {venue.average_rating && (
              <div className="info-item">
                <i className="fas fa-star"></i>
                <div>
                  <h3>Rating</h3>
                  <p>{venue.average_rating.toFixed(1)} / 5.0</p>
                </div>
              </div>
            )}
          </div>
        </Col>
      </Row>

      {/* Similar Venues Section */}
      <SimilarVenues venueId={venue.id} />
    </Container>
  );
};

export default VenueDetail;