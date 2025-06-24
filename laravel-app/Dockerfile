# Stage 1: Build Composer dependencies
FROM composer:2 AS composer_builder
WORKDIR /app
COPY composer.json composer.lock ./
RUN composer install --no-dev --no-scripts --no-autoloader

# Stage 2: Copy application code and configure Nginx/PHP-FPM
FROM php:8.2-fpm-alpine

# Install system dependencies and PHP extensions
RUN apk add --no-cache \
    nginx \
    php-pdo_mysql \
    php-mbstring \
    php-xml \
    php-json \
    php-curl \
    php-zip \
    php-gd \
    php-dom \
    php-session \
    php-redis \
    supervisor \
    git \
    # clean up cache after installing packages
    && rm -rf /var/cache/apk/*

# Set working directory
WORKDIR /var/www/html

# Copy Composer dependencies from builder stage
COPY --from=composer_builder /app/vendor /var/www/html/vendor

# Copy application source code
COPY . .

# Configure Nginx
COPY docker/nginx/default.conf /etc/nginx/http.d/default.conf

# Configure Supervisor
COPY docker/supervisor/supervisord.conf /etc/supervisord.conf

# Set proper permissions for Laravel
RUN chown -R www-data:www-data /var/www/html/storage \
    && chown -R www-data:www-data /var/www/html/bootstrap/cache \
    && chmod -R 775 /var/www/html/storage \
    && chmod -R 775 /var/www/html/bootstrap/cache

# Expose port 80 for Nginx
EXPOSE 80

# Start Nginx and PHP-FPM using Supervisor
CMD ["supervisord", "-c", "/etc/supervisord.conf"]
