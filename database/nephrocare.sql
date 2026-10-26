CREATE DATABASE IF NOT EXISTS nephrocare;
USE nephrocare;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fullname VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    mobile VARCHAR(15) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS prediction_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    fullname VARCHAR(100) NOT NULL,
    hemo DECIMAL(6,2) NOT NULL,
    al DECIMAL(6,2) NOT NULL,
    sg DECIMAL(6,3) NOT NULL,
    sc DECIMAL(6,2) NOT NULL,
    pcv DECIMAL(6,2) NOT NULL,
    htn VARCHAR(10) NOT NULL,
    prediction VARCHAR(100) NOT NULL,
    risk VARCHAR(20) NOT NULL,
    confidence VARCHAR(20) NOT NULL,
    probability DECIMAL(8,4) NOT NULL,
    prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_prediction_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_prediction_user_date (user_id, prediction_date)
);
