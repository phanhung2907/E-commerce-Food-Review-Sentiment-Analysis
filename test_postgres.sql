-- test_postgres.sql
-- Simple test schema + sample data for CloudBeaver/PostgreSQL

DROP TABLE IF EXISTS reviews;
DROP TABLE IF EXISTS restaurants;

CREATE TABLE restaurants (
    restaurant_id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    city VARCHAR(100),
    source VARCHAR(50)
);

CREATE TABLE reviews (
    review_id SERIAL PRIMARY KEY,
    restaurant_id INT NOT NULL,
    rating NUMERIC(2,1) CHECK (rating >= 1 AND rating <= 5),
    review_text TEXT,
    review_date DATE,
    CONSTRAINT fk_restaurant
        FOREIGN KEY (restaurant_id)
        REFERENCES restaurants(restaurant_id)
        ON DELETE CASCADE
);

INSERT INTO restaurants (name, city, source)
VALUES
    ('Test Restaurant A', 'Quy Nhon', 'shopeefood'),
    ('Test Restaurant B', 'Da Nang', 'tripadvisor');

INSERT INTO reviews (restaurant_id, rating, review_text, review_date)
VALUES
    (1, 5.0, 'Mon ngon, phuc vu tot', CURRENT_DATE),
    (1, 2.0, 'Giao hang cham', CURRENT_DATE),
    (2, 4.0, 'Khong gian dep', CURRENT_DATE);

SELECT * FROM restaurants;
SELECT * FROM reviews;

SELECT
    r.name,
    AVG(rv.rating) AS avg_rating,
    COUNT(rv.review_id) AS review_count
FROM restaurants r
LEFT JOIN reviews rv
    ON r.restaurant_id = rv.restaurant_id
GROUP BY r.restaurant_id, r.name
ORDER BY r.restaurant_id;
