/**
 * THABZO EVENTS - Analytics JavaScript
 * Handles tracking, analytics, and user behavior
 */

$(document).ready(function() {

    // ===== Google Analytics Setup =====
    (function() {
        var gaScript = document.createElement('script');
        gaScript.async = true;
        gaScript.src = 'https://www.googletagmanager.com/gtag/js?id=UA-XXXXXXXX-X';
        document.head.appendChild(gaScript);

        window.dataLayer = window.dataLayer || [];
        function gtag() {
            dataLayer.push(arguments);
        }
        gtag('js', new Date());
        gtag('config', 'UA-XXXXXXXX-X');
        window.gtag = gtag;
    })();

    // ===== Facebook Pixel Setup =====
    (function() {
        !function(f,b,e,v,n,t,s) {
            if(f.fbq)return;
            n=f.fbq=function(){n.callMethod? n.callMethod.apply(n,arguments):n.queue.push(arguments)};
            if(!f._fbq)f._fbq=n;
            n.push=n;n.loaded=!0;n.version='2.0';
            n.queue=[];t=b.createElement(e);t.async=!0;
            t.src=v;s=b.getElementsByTagName(e)[0];
            s.parentNode.insertBefore(t,s)
        }(window, document,'script','https://connect.facebook.net/en_US/fbevents.js');
        fbq('init', 'XXXXXXXXXXXXXXXXX');
        fbq('track', 'PageView');
        window.fbq = fbq;
    })();

    // ===== Track Page Views =====
    trackPageView();

    function trackPageView() {
        if (typeof gtag !== 'undefined') {
            gtag('event', 'page_view', {
                page_title: document.title,
                page_location: window.location.href,
                page_path: window.location.pathname
            });
        }

        if (typeof fbq !== 'undefined') {
            fbq('track', 'PageView');
        }
    }

    // ===== Track Outbound Links =====
    $('a[href^="http"]').not('a[href*="' + window.location.hostname + '"]').on('click', function() {
        var href = $(this).attr('href');
        var label = href.replace(/^https?:\/\//, '');

        if (typeof gtag !== 'undefined') {
            gtag('event', 'click', {
                'event_category': 'Outbound Link',
                'event_label': label
            });
        }

        if (typeof fbq !== 'undefined') {
            fbq('track', 'Click', {
                'content_name': 'Outbound Link',
                'content_category': label
            });
        }
    });

    // ===== Track Downloads =====
    $('a[download]').on('click', function() {
        var filename = $(this).attr('download') || $(this).attr('href').split('/').pop();

        if (typeof gtag !== 'undefined') {
            gtag('event', 'download', {
                'event_category': 'Download',
                'event_label': filename
            });
        }

        if (typeof fbq !== 'undefined') {
            fbq('track', 'Download', {
                'content_name': filename
            });
        }
    });

    // ===== Track Form Submissions =====
    $('form').on('submit', function() {
        var formId = $(this).attr('id') || 'form';
        var formName = $(this).attr('name') || formId;

        setTimeout(function() {
            if (typeof gtag !== 'undefined') {
                gtag('event', 'form_submit', {
                    'event_category': 'Form',
                    'event_label': formName
                });
            }

            if (typeof fbq !== 'undefined') {
                fbq('track', 'Lead', {
                    'content_name': formName
                });
            }
        }, 1000);
    });

    // ===== Track WhatsApp Clicks =====
    $('a[href*="wa.me"]').on('click', function() {
        var phone = $(this).attr('href').replace(/.*wa.me\//, '').split('?')[0];

        if (typeof gtag !== 'undefined') {
            gtag('event', 'whatsapp_click', {
                'event_category': 'WhatsApp',
                'event_label': phone
            });
        }

        if (typeof fbq !== 'undefined') {
            fbq('track', 'Lead', {
                'content_name': 'WhatsApp Click',
                'content_category': phone
            });
        }
    });

    // ===== Track Phone Clicks =====
    $('a[href^="tel:"]').on('click', function() {
        var phone = $(this).attr('href').replace('tel:', '');

        if (typeof gtag !== 'undefined') {
            gtag('event', 'phone_click', {
                'event_category': 'Phone',
                'event_label': phone
            });
        }

        if (typeof fbq !== 'undefined') {
            fbq('track', 'Lead', {
                'content_name': 'Phone Call',
                'content_category': phone
            });
        }
    });

    // ===== Track Email Clicks =====
    $('a[href^="mailto:"]').on('click', function() {
        var email = $(this).attr('href').replace('mailto:', '');

        if (typeof gtag !== 'undefined') {
            gtag('event', 'email_click', {
                'event_category': 'Email',
                'event_label': email
            });
        }
    });

    // ===== Track Scroll Depth =====
    var scrollPercentages = [25, 50, 75, 100];
    var scrolled = {};

    $(window).on('scroll', function() {
        var scrollTop = $(window).scrollTop();
        var docHeight = $(document).height() - $(window).height();
        var scrollPercent = (scrollTop / docHeight) * 100;

        scrollPercentages.forEach(function(percent) {
            if (scrollPercent >= percent && !scrolled[percent]) {
                scrolled[percent] = true;

                if (typeof gtag !== 'undefined') {
                    gtag('event', 'scroll_depth', {
                        'event_category': 'Scroll',
                        'event_label': percent + '%'
                    });
                }
            }
        });
    });

    // ===== Track Time on Page =====
    var timeOnPage = 0;
    var timeInterval = setInterval(function() {
        timeOnPage += 1;
    }, 1000);

    $(window).on('beforeunload', function() {
        clearInterval(timeInterval);

        if (timeOnPage > 10) {
            if (typeof gtag !== 'undefined') {
                gtag('event', 'time_on_page', {
                    'event_category': 'Engagement',
                    'event_label': timeOnPage + ' seconds'
                });
            }
        }
    });

    // ===== Track Video Engagement =====
    $('video').each(function() {
        var video = this;
        var videoId = $(video).attr('id') || 'video';

        video.addEventListener('play', function() {
            if (typeof gtag !== 'undefined') {
                gtag('event', 'video_play', {
                    'event_category': 'Video',
                    'event_label': videoId
                });
            }
        });

        video.addEventListener('ended', function() {
            if (typeof gtag !== 'undefined') {
                gtag('event', 'video_complete', {
                    'event_category': 'Video',
                    'event_label': videoId
                });
            }
        });
    });

    // ===== Track Social Sharing =====
    $('.share-btn').on('click', function() {
        var platform = $(this).data('platform') || 'unknown';
        var url = $(this).data('url') || window.location.href;

        if (typeof gtag !== 'undefined') {
            gtag('event', 'share', {
                'event_category': 'Social',
                'event_label': platform,
                'event_value': url
            });
        }
    });

    // ===== Track Search Queries =====
    var searchInputs = $('input[type="search"], .search-input');
    searchInputs.on('keydown', function(e) {
        if (e.key === 'Enter') {
            var query = $(this).val();

            if (typeof gtag !== 'undefined') {
                gtag('event', 'search', {
                    'event_category': 'Search',
                    'event_label': query
                });
            }
        }
    });

    // ===== Track Error Events =====
    window.addEventListener('error', function(e) {
        if (typeof gtag !== 'undefined') {
            gtag('event', 'error', {
                'event_category': 'JavaScript',
                'event_label': e.message,
                'event_value': e.lineno
            });
        }
    });

    // ===== Track User Engagement =====
    var engagementEvents = ['click', 'mousedown', 'keydown', 'touchstart'];
    var engaged = false;

    engagementEvents.forEach(function(eventType) {
        $(document).on(eventType, function() {
            if (!engaged) {
                engaged = true;
                if (typeof gtag !== 'undefined') {
                    gtag('event', 'user_engaged', {
                        'event_category': 'Engagement',
                        'event_label': 'First Interaction'
                    });
                }
            }
        });
    });

    // ===== Track Bounce Rate =====
    // Track when user leaves after viewing only one page
    var visitedPages = [];

    $(window).on('beforeunload', function() {
        var currentUrl = window.location.pathname;
        visitedPages.push(currentUrl);

        if (visitedPages.length === 1) {
            // User is leaving after viewing only this page
            setTimeout(function() {
                if (typeof gtag !== 'undefined') {
                    gtag('event', 'bounce', {
                        'event_category': 'Engagement',
                        'event_label': currentUrl
                    });
                }
            }, 1000);
        }
    });

    // ===== Track E-commerce =====
    function trackAddToCart(product, quantity, price) {
        if (typeof gtag !== 'undefined') {
            gtag('event', 'add_to_cart', {
                'items': [{
                    'id': product.id || '',
                    'name': product.name || '',
                    'category': product.category || '',
                    'quantity': quantity || 1,
                    'price': price || 0
                }]
            });
        }
    }

    function trackPurchase(transaction) {
        if (typeof gtag !== 'undefined') {
            gtag('event', 'purchase', {
                'transaction_id': transaction.id || '',
                'value': transaction.total || 0,
                'currency': 'ZAR',
                'items': transaction.items || []
            });
        }
    }

    // ===== Expose tracking functions globally =====
    window.trackPageView = trackPageView;
    window.trackAddToCart = trackAddToCart;
    window.trackPurchase = trackPurchase;
});