/**
 * THABZO EVENTS - WhatsApp Widget
 */

$(document).ready(function() {

    // ===== WhatsApp Floating Button =====
    var whatsappButton = $('.whatsapp-float');

    if (whatsappButton.length) {
        // Predefined messages based on page
        var pageMessages = {
            'index': 'Hi THABZO EVENTS! I found your website and would like to inquire about your decoration services.',
            'about': 'Hi THABZO EVENTS! I read about your company and would like to know more about your services.',
            'services': 'Hi THABZO EVENTS! I\'m interested in your decoration services and would like a quote.',
            'gallery': 'Hi THABZO EVENTS! I saw your beautiful gallery and would like to inquire about your services.',
            'testimonials': 'Hi THABZO EVENTS! I read the testimonials and would like to inquire about your services.',
            'contact': 'Hi THABZO EVENTS! I\'m contacting you through your website for a quote.'
        };

        var currentPage = getCurrentPage();
        var message = pageMessages[currentPage] || 'Hi THABZO EVENTS! I found your website and would like to inquire about your services.';

        // Update WhatsApp link with message
        var phoneNumber = whatsappButton.attr('href').replace('https://wa.me/', '').replace(/\/.*$/, '');
        var encodedMessage = encodeURIComponent(message);
        whatsappButton.attr('href', 'https://wa.me/' + phoneNumber + '?text=' + encodedMessage);
    }

    // ===== WhatsApp Chat Widget =====
    $('.whatsapp-chat').each(function() {
        var $this = $(this);
        var phoneNumber = $this.data('phone') || '';
        var message = $this.data('message') || 'Hi THABZO EVENTS! I would like to inquire about your services.';
        var encodedMessage = encodeURIComponent(message);

        $this.attr('href', 'https://wa.me/' + phoneNumber + '?text=' + encodedMessage);
    });

    // ===== Quick WhatsApp Contact =====
    $('.whatsapp-quick').on('click', function(e) {
        var $this = $(this);
        var phone = $this.data('phone');
        var message = $this.data('message') || 'Hi THABZO EVENTS! I have a question.';
        var encodedMessage = encodeURIComponent(message);

        window.open('https://wa.me/' + phone + '?text=' + encodedMessage, '_blank');
    });

    // ===== WhatsApp Form Integration =====
    $('#whatsappForm').on('submit', function(e) {
        e.preventDefault();
        var phone = $(this).data('phone');
        var name = $('#name').val();
        var email = $('#email').val();
        var message = $('#message').val();

        var whatsappMessage = 'Hello THABZO EVENTS,\n\n';
        whatsappMessage += 'Name: ' + name + '\n';
        whatsappMessage += 'Email: ' + email + '\n\n';
        whatsappMessage += 'Message: ' + message;

        var encodedMessage = encodeURIComponent(whatsappMessage);
        window.open('https://wa.me/' + phone + '?text=' + encodedMessage, '_blank');
    });

    // ===== Get current page =====
    function getCurrentPage() {
        var path = window.location.pathname;
        var page = 'index';

        if (path.includes('/about')) page = 'about';
        else if (path.includes('/services')) page = 'services';
        else if (path.includes('/gallery')) page = 'gallery';
        else if (path.includes('/testimonials')) page = 'testimonials';
        else if (path.includes('/contact')) page = 'contact';

        return page;
    }

    // ===== Track WhatsApp Clicks =====
    $('.whatsapp-float, .whatsapp-btn, .whatsapp-chat, .whatsapp-quick').on('click', function() {
        // Track for analytics
        if (typeof gtag !== 'undefined') {
            gtag('event', 'conversion', {
                'send_to': 'AW-XXXXXXXX/XXXXXXXX',
                'event_category': 'WhatsApp',
                'event_label': 'WhatsApp Click'
            });
        }

        if (typeof fbq !== 'undefined') {
            fbq('track', 'Lead', {
                'content_name': 'WhatsApp Click'
            });
        }
    });

    // ===== WhatsApp Status =====
    function checkWhatsAppStatus() {
        // You can implement a status check here
        // This could ping a service to check if WhatsApp is available
        return true;
    }

    // ===== Dynamic WhatsApp Number =====
    // You can change the WhatsApp number dynamically based on conditions
    function setWhatsAppNumber(phoneNumber) {
        var whatsappLinks = $('a[href*="wa.me"]');
        whatsappLinks.each(function() {
            var href = $(this).attr('href');
            var hasText = href.includes('?text=');
            var text = '';
            if (hasText) {
                text = href.split('?text=')[1];
            }
            if (text) {
                $(this).attr('href', 'https://wa.me/' + phoneNumber + '?text=' + text);
            } else {
                $(this).attr('href', 'https://wa.me/' + phoneNumber);
            }
        });
    }
});