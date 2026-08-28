/**
 * THABZO EVENTS - Testimonials JavaScript
 * Handles testimonials carousel, filtering, and display
 */

$(document).ready(function() {

    // ===== Testimonials Carousel =====
    function initTestimonialCarousel() {
        var container = $('.testimonials-carousel');
        if (!container.length) return;

        var slides = container.find('.testimonial-card');
        if (slides.length <= 1) {
            slides.show();
            return;
        }

        var currentIndex = 0;
        var totalSlides = slides.length;
        var autoplayInterval;
        var isPlaying = true;
        var slideDuration = 5000;

        // Hide all slides except first
        slides.hide();
        slides.eq(0).show();

        // Create navigation dots
        var dotsContainer = $('<div class="carousel-dots"></div>');
        for (var i = 0; i < totalSlides; i++) {
            var dot = $('<span class="dot" data-index="' + i + '"></span>');
            if (i === 0) dot.addClass('active');
            dotsContainer.append(dot);
        }
        container.after(dotsContainer);

        // Create navigation arrows
        var navContainer = $('<div class="carousel-nav"></div>');
        navContainer.html(`
            <button class="carousel-prev" aria-label="Previous"><i class="fas fa-chevron-left"></i></button>
            <button class="carousel-next" aria-label="Next"><i class="fas fa-chevron-right"></i></button>
        `);
        container.after(navContainer);

        // Function to go to a specific slide
        function goToSlide(index) {
            // Validate index
            if (index < 0) index = totalSlides - 1;
            if (index >= totalSlides) index = 0;

            // Fade out current slide
            slides.eq(currentIndex).fadeOut(300, function() {
                // Update index
                currentIndex = index;
                // Fade in new slide
                slides.eq(currentIndex).fadeIn(300);
                // Update dots
                $('.carousel-dots .dot').removeClass('active');
                $('.carousel-dots .dot[data-index="' + currentIndex + '"]').addClass('active');
            });
        }

        // Next slide
        function nextSlide() {
            goToSlide(currentIndex + 1);
        }

        // Previous slide
        function prevSlide() {
            goToSlide(currentIndex - 1);
        }

        // Start autoplay
        function startAutoplay() {
            if (autoplayInterval) clearInterval(autoplayInterval);
            autoplayInterval = setInterval(nextSlide, slideDuration);
            isPlaying = true;
        }

        // Stop autoplay
        function stopAutoplay() {
            if (autoplayInterval) {
                clearInterval(autoplayInterval);
                autoplayInterval = null;
            }
            isPlaying = false;
        }

        // Toggle autoplay
        function toggleAutoplay() {
            if (isPlaying) {
                stopAutoplay();
            } else {
                startAutoplay();
            }
        }

        // Event listeners
        $('.carousel-next').on('click', function() {
            nextSlide();
            stopAutoplay();
            // Restart autoplay after user interaction
            setTimeout(startAutoplay, 3000);
        });

        $('.carousel-prev').on('click', function() {
            prevSlide();
            stopAutoplay();
            setTimeout(startAutoplay, 3000);
        });

        $('.carousel-dots .dot').on('click', function() {
            var index = parseInt($(this).data('index'));
            goToSlide(index);
            stopAutoplay();
            setTimeout(startAutoplay, 3000);
        });

        // Pause on hover
        container.hover(stopAutoplay, startAutoplay);

        // Keyboard navigation
        $(document).on('keydown', function(e) {
            if (container.is(':visible')) {
                if (e.key === 'ArrowRight') {
                    nextSlide();
                    stopAutoplay();
                    setTimeout(startAutoplay, 3000);
                } else if (e.key === 'ArrowLeft') {
                    prevSlide();
                    stopAutoplay();
                    setTimeout(startAutoplay, 3000);
                }
            }
        });

        // Start autoplay
        startAutoplay();
    }

    // ===== Initialize Carousel =====
    initTestimonialCarousel();

    // ===== Testimonials Filter =====
    $('.testimonials-filter .filter-btn').on('click', function() {
        var filter = $(this).data('filter');

        $('.testimonials-filter .filter-btn').removeClass('active');
        $(this).addClass('active');

        $('.testimonial-card').each(function() {
            var $card = $(this);
            if (filter === 'all' || $card.data('rating') === parseInt(filter)) {
                $card.show();
                $card.addClass('fade-in');
            } else {
                $card.hide();
                $card.removeClass('fade-in');
            }
        });
    });

    // ===== Load More Testimonials =====
    var loadMoreBtn = $('#loadMoreTestimonials');
    var currentPage = 1;
    var loading = false;

    loadMoreBtn.on('click', function() {
        if (loading) return;
        loading = true;
        loadMoreBtn.text('Loading...');
        loadMoreBtn.prop('disabled', true);

        var rating = $('.testimonials-filter .filter-btn.active').data('filter') || 'all';

        $.ajax({
            url: '/testimonials/load-more',
            method: 'GET',
            data: {
                page: currentPage + 1,
                rating: rating
            },
            success: function(response) {
                if (response.html) {
                    $('.testimonials-grid').append(response.html);
                    currentPage = response.page;

                    if (!response.hasMore) {
                        loadMoreBtn.hide();
                    } else {
                        loadMoreBtn.text('Load More');
                        loadMoreBtn.prop('disabled', false);
                    }
                } else {
                    loadMoreBtn.hide();
                }
                loading = false;
            },
            error: function() {
                loadMoreBtn.text('Try Again');
                loadMoreBtn.prop('disabled', false);
                loading = false;
            }
        });
    });

    // ===== Rating Stars Animation =====
    function animateStars() {
        $('.testimonial-stars .fa-star').each(function(index) {
            var $star = $(this);
            setTimeout(function() {
                $star.addClass('star-animate');
            }, index * 100);
        });
    }

    // ===== Testimonial Form =====
    $('#testimonialForm').on('submit', function(e) {
        e.preventDefault();
        var $form = $(this);
        var data = $form.serialize();

        // Show loading
        var submitBtn = $form.find('[type="submit"]');
        var originalText = submitBtn.html();
        submitBtn.html('<i class="fas fa-spinner fa-spin"></i> Submitting...');
        submitBtn.prop('disabled', true);

        $.ajax({
            url: $form.attr('action'),
            method: 'POST',
            data: data,
            success: function(response) {
                if (response.success) {
                    showNotification('Thank you for your testimonial! It will be reviewed and published soon.', 'success');
                    $form.trigger('reset');
                    // Reset rating
                    $('.rating-input .fa-star').removeClass('active');
                } else {
                    showNotification(response.message || 'An error occurred.', 'danger');
                }
                submitBtn.html(originalText);
                submitBtn.prop('disabled', false);
            },
            error: function() {
                showNotification('An error occurred. Please try again.', 'danger');
                submitBtn.html(originalText);
                submitBtn.prop('disabled', false);
            }
        });
    });

    // ===== Rating Input =====
    $('.rating-input .fa-star').on('mouseenter', function() {
        var index = $(this).data('index');
        $('.rating-input .fa-star').each(function(i) {
            if (i <= index) {
                $(this).addClass('hover');
            } else {
                $(this).removeClass('hover');
            }
        });
    });

    $('.rating-input').on('mouseleave', function() {
        $('.rating-input .fa-star').removeClass('hover');
    });

    $('.rating-input .fa-star').on('click', function() {
        var index = $(this).data('index');
        $('.rating-input .fa-star').removeClass('active');
        $('.rating-input .fa-star').each(function(i) {
            if (i <= index) {
                $(this).addClass('active');
            }
        });
        $('#ratingValue').val(index + 1);
    });

    // ===== Testimonial Search =====
    var searchInput = $('#testimonialSearch');
    var searchTimeout;

    searchInput.on('input', function() {
        clearTimeout(searchTimeout);
        var query = $(this).val().toLowerCase().trim();

        searchTimeout = setTimeout(function() {
            $('.testimonial-card').each(function() {
                var $card = $(this);
                var content = $card.find('.testimonial-content').text().toLowerCase();
                var author = $card.find('.author-info strong').text().toLowerCase();
                var eventType = $card.find('.author-info span').text().toLowerCase();

                var match = content.includes(query) || author.includes(query) || eventType.includes(query);
                $card.toggle(match);
                if (match) $card.addClass('fade-in');
            });
        }, 300);
    });

    // ===== Share Testimonial =====
    $('.share-testimonial').on('click', function() {
        var $card = $(this).closest('.testimonial-card');
        var content = $card.find('.testimonial-content').text();
        var author = $card.find('.author-info strong').text();

        var shareText = '"' + content + '" - ' + author + ' | THABZO EVENTS';

        if (navigator.share) {
            navigator.share({
                title: 'Testimonial - THABZO EVENTS',
                text: shareText,
                url: window.location.href
            }).catch(function() {});
        } else {
            // Copy to clipboard
            navigator.clipboard.writeText(shareText).then(function() {
                showNotification('Testimonial copied to clipboard!', 'success');
            });
        }
    });

    // ===== Notification System =====
    function showNotification(message, type) {
        var alertClass = {
            success: 'alert-success',
            danger: 'alert-danger',
            warning: 'alert-warning',
            info: 'alert-info'
        }[type] || 'alert-info';

        var icon = {
            success: 'fa-check-circle',
            danger: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        }[type] || 'fa-info-circle';

        var html = '<div class="alert ' + alertClass + ' alert-dismissible fade show" style="position: fixed; top: 20px; right: 20px; z-index: 9999; max-width: 400px; box-shadow: 0 4px 20px rgba(0,0,0,0.15);">' +
            '<i class="fas ' + icon + '"></i> ' + message +
            '<button type="button" class="alert-close" data-dismiss="alert">&times;</button>' +
            '</div>';

        $('body').append(html);

        setTimeout(function() {
            $('.alert').fadeOut(500, function() {
                $(this).remove();
            });
        }, 5000);
    }

    // ===== Initialize animations =====
    animateStars();
});

// ===== Carousel Styles =====
$(document).ready(function() {
    var style = `
        .carousel-dots {
            text-align: center;
            margin-top: 20px;
        }
        .carousel-dots .dot {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #ddd;
            margin: 0 5px;
            cursor: pointer;
            transition: background 0.3s ease;
        }
        .carousel-dots .dot.active {
            background: #6c5ce7;
        }
        .carousel-dots .dot:hover {
            background: #6c5ce7;
        }
        .carousel-nav {
            text-align: center;
            margin-top: 15px;
        }
        .carousel-nav button {
            background: #fff;
            border: 2px solid #6c5ce7;
            color: #6c5ce7;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            cursor: pointer;
            margin: 0 5px;
            transition: all 0.3s ease;
        }
        .carousel-nav button:hover {
            background: #6c5ce7;
            color: #fff;
        }
        .star-animate {
            animation: starPulse 0.5s ease;
        }
        @keyframes starPulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.3); color: #f39c12; }
            100% { transform: scale(1); }
        }
        .rating-input .fa-star {
            font-size: 28px;
            color: #ddd;
            cursor: pointer;
            transition: all 0.2s ease;
            margin: 0 3px;
        }
        .rating-input .fa-star:hover,
        .rating-input .fa-star.hover,
        .rating-input .fa-star.active {
            color: #f39c12;
        }
        .rating-input .fa-star.active {
            animation: starPulse 0.5s ease;
        }
    `;
    $('<style>').html(style).appendTo('head');
});