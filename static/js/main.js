/**
 * THABZO EVENTS - Main JavaScript
 */

$(document).ready(function() {

    // ===== Navbar Scroll Effect =====
    $(window).on('scroll', function() {
        var scroll = $(window).scrollTop();
        if (scroll > 50) {
            $('.navbar').addClass('scrolled');
        } else {
            $('.navbar').removeClass('scrolled');
        }

        // Scroll to top button
        if (scroll > 300) {
            $('#scrollTop').addClass('visible');
        } else {
            $('#scrollTop').removeClass('visible');
        }
    });

    // ===== Navbar Toggle =====
    $('.navbar-toggler').on('click', function() {
        $('.navbar-collapse').toggleClass('show');
    });

    // Close navbar on link click (mobile)
    $('.nav-link').on('click', function() {
        $('.navbar-collapse').removeClass('show');
    });

    // ===== Scroll to Top =====
    $('#scrollTop').on('click', function() {
        $('html, body').animate({
            scrollTop: 0
        }, 600);
    });

    // ===== Smooth Scroll for Anchor Links =====
    $('a[href^="#"]:not([href="#"])').on('click', function(e) {
        var target = $(this.hash);
        if (target.length) {
            e.preventDefault();
            $('html, body').animate({
                scrollTop: target.offset().top - 80
            }, 800);
        }
    });

    // ===== Alert Dismiss =====
    $('.alert-close').on('click', function() {
        $(this).closest('.alert').fadeOut(300);
    });

    // ===== Auto-dismiss alerts after 5 seconds =====
    setTimeout(function() {
        $('.alert').fadeOut(500);
    }, 5000);

    // ===== Gallery Zoom (Lightbox) =====
    $('.gallery-zoom').on('click', function(e) {
        e.preventDefault();
        var imgSrc = $(this).attr('href');
        $('#lightbox-img').attr('src', imgSrc);
        $('#lightbox').fadeIn(300);
    });

    // Close lightbox
    $('.lightbox-close, #lightbox').on('click', function(e) {
        if (e.target === this) {
            $('#lightbox').fadeOut(300);
        }
    });

    // Close lightbox with Escape key
    $(document).on('keydown', function(e) {
        if (e.key === 'Escape') {
            $('#lightbox').fadeOut(300);
        }
    });

    // ===== Form Validation =====
    $('form').on('submit', function(e) {
        var $form = $(this);
        var isValid = true;

        $form.find('.form-control[required]').each(function() {
            if (!$(this).val().trim()) {
                $(this).addClass('is-invalid');
                isValid = false;
            } else {
                $(this).removeClass('is-invalid');
            }
        });

        // Email validation
        $form.find('input[type="email"]').each(function() {
            var email = $(this).val().trim();
            if (email && !isValidEmail(email)) {
                $(this).addClass('is-invalid');
                isValid = false;
            }
        });

        if (!isValid) {
            e.preventDefault();
            $('html, body').animate({
                scrollTop: $('.is-invalid:first').offset().top - 100
            }, 500);
        }
    });

    // Remove invalid class on input
    $('.form-control').on('input', function() {
        $(this).removeClass('is-invalid');
    });

    // ===== Email Validation Helper =====
    function isValidEmail(email) {
        var re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }

    // ===== WhatsApp Click Tracking =====
    $('.whatsapp-float, .whatsapp-btn').on('click', function() {
        // Track WhatsApp clicks (for analytics)
        if (typeof gtag !== 'undefined') {
            gtag('event', 'click', {
                'event_category': 'WhatsApp',
                'event_label': 'WhatsApp Click'
            });
        }
    });

    // ===== Phone Click Tracking =====
    $('a[href^="tel:"]').on('click', function() {
        if (typeof gtag !== 'undefined') {
            gtag('event', 'click', {
                'event_category': 'Phone',
                'event_label': 'Phone Call'
            });
        }
    });

    // ===== Lazy Loading Images =====
    if ('IntersectionObserver' in window) {
        var lazyImages = document.querySelectorAll('img[loading="lazy"]');
        var imageObserver = new IntersectionObserver(function(entries) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    var img = entry.target;
                    img.src = img.dataset.src || img.src;
                    imageObserver.unobserve(img);
                }
            });
        });

        lazyImages.forEach(function(img) {
            imageObserver.observe(img);
        });
    }

    // ===== Testimonial Carousel =====
    var testimonialCarousel = $('.testimonials-carousel');
    if (testimonialCarousel.length) {
        var items = testimonialCarousel.find('.testimonial-card');
        if (items.length > 1) {
            var currentIndex = 0;
            var totalItems = items.length;

            // Show first item
            items.hide();
            items.eq(0).show();

            // Auto rotate
            setInterval(function() {
                items.fadeOut(300);
                currentIndex = (currentIndex + 1) % totalItems;
                items.eq(currentIndex).fadeIn(300);
            }, 5000);
        }
    }

    // ===== Service Filter =====
    $('.filter-btn').on('click', function() {
        var filter = $(this).data('filter');

        $('.filter-btn').removeClass('active');
        $(this).addClass('active');

        $('.service-card, .gallery-item').each(function() {
            if (filter === 'all' || $(this).data('category') === filter) {
                $(this).show();
            } else {
                $(this).hide();
            }
        });
    });

    // ===== Copy to Clipboard =====
    $('.copy-btn').on('click', function() {
        var text = $(this).data('copy');
        navigator.clipboard.writeText(text).then(function() {
            $(this).text('Copied!');
            setTimeout(function() {
                $(this).text('Copy');
            }, 2000);
        }.bind(this));
    });

    // ===== Phone Number Formatting =====
    function formatPhoneNumber(phone) {
        // Remove all non-numeric characters
        var cleaned = phone.replace(/\D/g, '');
        // Format as 076 584 1224
        if (cleaned.length === 10) {
            return cleaned.replace(/(\d{3})(\d{3})(\d{4})/, '$1 $2 $3');
        }
        return phone;
    }

    // ===== Google Maps Integration (if needed) =====
    function initMap() {
        var location = { lat: -27.4185, lng: 32.0654 }; // Jozini coordinates
        var map = new google.maps.Map(document.getElementById('map'), {
            zoom: 13,
            center: location
        });
        var marker = new google.maps.Marker({
            position: location,
            map: map,
            title: 'THABZO EVENTS'
        });
    }

    // ===== Cookie Consent =====
    if (!localStorage.getItem('cookieConsent')) {
        // Show cookie consent if not already accepted
        // (Implementation depends on your cookie policy)
    }

    // ===== Service Worker Registration (PWA) =====
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js')
            .then(function(registration) {
                console.log('ServiceWorker registration successful');
            })
            .catch(function(error) {
                console.log('ServiceWorker registration failed:', error);
            });
    }

    // ===== Check if mobile device =====
    function isMobileDevice() {
        return window.innerWidth <= 768;
    }

    // ===== Back to top button visibility =====
    var scrollTop = $('#scrollTop');
    $(window).on('scroll', function() {
        if ($(window).scrollTop() > 300) {
            scrollTop.addClass('visible');
        } else {
            scrollTop.removeClass('visible');
        }
    });
});

// ===== Expose functions globally =====
window.isValidEmail = function(email) {
    var re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
};

window.formatPhoneNumber = function(phone) {
    var cleaned = phone.replace(/\D/g, '');
    if (cleaned.length === 10) {
        return cleaned.replace(/(\d{3})(\d{3})(\d{4})/, '$1 $2 $3');
    }
    return phone;
};