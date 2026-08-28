/**
 * THABZO EVENTS - Services JavaScript
 * Handles services interactions, filtering, and pricing
 */

$(document).ready(function() {

    // ===== Service Categories Filter =====
    $('.service-filter .filter-btn').on('click', function() {
        var filter = $(this).data('filter');

        $('.service-filter .filter-btn').removeClass('active');
        $(this).addClass('active');

        $('.service-card').each(function() {
            var $card = $(this);
            if (filter === 'all' || $card.data('category') === filter) {
                $card.show();
                $card.addClass('fade-in');
            } else {
                $card.hide();
                $card.removeClass('fade-in');
            }
        });
    });

    // ===== Price Range Slider =====
    var priceSlider = $('#priceRange');
    if (priceSlider.length) {
        var minPrice = parseInt(priceSlider.data('min')) || 0;
        var maxPrice = parseInt(priceSlider.data('max')) || 50000;
        var step = parseInt(priceSlider.data('step')) || 1000;

        priceSlider.slider({
            range: true,
            min: minPrice,
            max: maxPrice,
            step: step,
            values: [minPrice, maxPrice],
            slide: function(event, ui) {
                $('#priceMin').text('R' + ui.values[0].toLocaleString());
                $('#priceMax').text('R' + ui.values[1].toLocaleString());
                filterByPrice(ui.values[0], ui.values[1]);
            }
        });
    }

    function filterByPrice(min, max) {
        $('.service-card').each(function() {
            var $card = $(this);
            var price = parseInt($card.data('price')) || 0;
            if (price >= min && price <= max) {
                $card.show();
                $card.addClass('fade-in');
            } else {
                $card.hide();
                $card.removeClass('fade-in');
            }
        });
    }

    // ===== Service Search =====
    var searchInput = $('#serviceSearch');
    var searchTimeout;

    searchInput.on('input', function() {
        clearTimeout(searchTimeout);
        var query = $(this).val().toLowerCase().trim();

        searchTimeout = setTimeout(function() {
            $('.service-card').each(function() {
                var $card = $(this);
                var name = $card.find('.service-name').text().toLowerCase();
                var desc = $card.find('.service-description').text().toLowerCase();
                var category = $card.data('category') || '';

                var match = name.includes(query) || desc.includes(query) || category.includes(query);
                $card.toggle(match);
                if (match) $card.addClass('fade-in');
            });
        }, 300);
    });

    // ===== Service Details Toggle =====
    $('.service-detail-toggle').on('click', function() {
        var $card = $(this).closest('.service-card');
        var $details = $card.find('.service-details');
        var $icon = $(this).find('i');

        if ($details.is(':visible')) {
            $details.slideUp(300);
            $icon.removeClass('fa-chevron-up').addClass('fa-chevron-down');
        } else {
            $details.slideDown(300);
            $icon.removeClass('fa-chevron-down').addClass('fa-chevron-up');
        }
    });

    // ===== Quick Estimate Calculator =====
    $('#estimateForm').on('submit', function(e) {
        e.preventDefault();
        var $form = $(this);
        var eventType = $('#estimateEventType').val();
        var guestCount = parseInt($('#estimateGuests').val()) || 0;
        var complexity = $('#estimateComplexity').val() || 'medium';
        var addOns = [];

        $('input[name="addons"]:checked').each(function() {
            addOns.push($(this).val());
        });

        if (!eventType) {
            showNotification('Please select an event type.', 'warning');
            return;
        }

        // Show loading
        var submitBtn = $form.find('[type="submit"]');
        var originalText = submitBtn.html();
        submitBtn.html('<i class="fas fa-spinner fa-spin"></i> Calculating...');
        submitBtn.prop('disabled', true);

        $.ajax({
            url: '/api/estimate',
            method: 'POST',
            data: JSON.stringify({
                event_type: eventType,
                guest_count: guestCount,
                complexity: complexity,
                add_ons: addOns
            }),
            contentType: 'application/json',
            success: function(response) {
                $('#estimateResult').show();
                $('#estimateAmount').text(response.estimate_display);
                $('#estimateRange').text(response.price_range_display);

                // Animate result
                $('#estimateResult').addClass('fade-in');

                submitBtn.html(originalText);
                submitBtn.prop('disabled', false);
            },
            error: function() {
                showNotification('Failed to calculate estimate. Please try again.', 'danger');
                submitBtn.html(originalText);
                submitBtn.prop('disabled', false);
            }
        });
    });

    // ===== Add to Quote =====
    $('.add-to-quote').on('click', function() {
        var $card = $(this).closest('.service-card');
        var serviceName = $card.find('.service-name').text();
        var servicePrice = $card.data('price') || 0;

        // Get existing quote items
        var quoteItems = JSON.parse(localStorage.getItem('quoteItems') || '[]');

        // Check if already in quote
        var existing = quoteItems.find(function(item) {
            return item.name === serviceName;
        });

        if (existing) {
            existing.quantity += 1;
        } else {
            quoteItems.push({
                name: serviceName,
                price: servicePrice,
                quantity: 1
            });
        }

        localStorage.setItem('quoteItems', JSON.stringify(quoteItems));

        // Update quote badge
        updateQuoteBadge();

        showNotification(serviceName + ' added to your quote!', 'success');
    });

    // ===== Update Quote Badge =====
    function updateQuoteBadge() {
        var quoteItems = JSON.parse(localStorage.getItem('quoteItems') || '[]');
        var count = quoteItems.reduce(function(total, item) {
            return total + item.quantity;
        }, 0);

        var badge = $('#quoteBadge');
        if (count > 0) {
            badge.text(count);
            badge.show();
        } else {
            badge.hide();
        }
    }

    // ===== View Quote =====
    $('#viewQuote').on('click', function() {
        var quoteItems = JSON.parse(localStorage.getItem('quoteItems') || '[]');

        if (quoteItems.length === 0) {
            showNotification('Your quote is empty. Add some services first!', 'warning');
            return;
        }

        var total = quoteItems.reduce(function(sum, item) {
            return sum + (item.price * item.quantity);
        }, 0);

        var html = '<div class="quote-popup"><h3>Your Quote</h3><table class="quote-table">';
        html += '<thead><tr><th>Service</th><th>Qty</th><th>Price</th><th>Total</th><th></th></tr></thead><tbody>';

        quoteItems.forEach(function(item, index) {
            var itemTotal = item.price * item.quantity;
            html += '<tr>';
            html += '<td>' + item.name + '</td>';
            html += '<td><button class="qty-btn" data-index="' + index + '" data-action="decrease">-</button> ' + item.quantity + ' <button class="qty-btn" data-index="' + index + '" data-action="increase">+</button></td>';
            html += '<td>R' + item.price.toLocaleString() + '</td>';
            html += '<td>R' + itemTotal.toLocaleString() + '</td>';
            html += '<td><button class="remove-item" data-index="' + index + '"><i class="fas fa-times"></i></button></td>';
            html += '</tr>';
        });

        html += '</tbody><tfoot><tr><td colspan="3"><strong>Total</strong></td><td><strong>R' + total.toLocaleString() + '</strong></td><td></td></tr></tfoot></table>';
        html += '<div class="quote-actions"><button class="btn btn-primary" id="requestQuote">Request Quote</button> <button class="btn btn-outline-secondary" id="clearQuote">Clear All</button></div></div>';

        // Show popup
        var popup = $('<div class="modal-overlay">' + html + '</div>');
        $('body').append(popup);

        // Handle quantity changes
        popup.find('.qty-btn').on('click', function() {
            var index = parseInt($(this).data('index'));
            var action = $(this).data('action');
            var items = JSON.parse(localStorage.getItem('quoteItems') || '[]');

            if (action === 'increase') {
                items[index].quantity += 1;
            } else if (action === 'decrease') {
                items[index].quantity -= 1;
                if (items[index].quantity <= 0) {
                    items.splice(index, 1);
                }
            }

            localStorage.setItem('quoteItems', JSON.stringify(items));
            updateQuoteBadge();
            popup.remove();
            $('#viewQuote').trigger('click');
        });

        // Remove item
        popup.find('.remove-item').on('click', function() {
            var index = parseInt($(this).data('index'));
            var items = JSON.parse(localStorage.getItem('quoteItems') || '[]');
            items.splice(index, 1);
            localStorage.setItem('quoteItems', JSON.stringify(items));
            updateQuoteBadge();
            popup.remove();
            $('#viewQuote').trigger('click');
        });

        // Clear all
        popup.find('#clearQuote').on('click', function() {
            localStorage.removeItem('quoteItems');
            updateQuoteBadge();
            popup.remove();
            showNotification('Quote cleared.', 'info');
        });

        // Request quote
        popup.find('#requestQuote').on('click', function() {
            var items = JSON.parse(localStorage.getItem('quoteItems') || '[]');
            var message = 'I would like to request a quote for the following services:\n\n';
            items.forEach(function(item) {
                message += '- ' + item.name + ' (x' + item.quantity + ')\n';
            });

            window.location.href = '/contact?message=' + encodeURIComponent(message);
        });

        // Close on background click
        popup.on('click', function(e) {
            if (e.target === this) {
                popup.remove();
            }
        });
    });

    // ===== Compare Services =====
    var compareList = [];

    $('.compare-service').on('click', function() {
        var $card = $(this).closest('.service-card');
        var serviceName = $card.find('.service-name').text();
        var servicePrice = $card.data('price') || 0;
        var serviceDesc = $card.find('.service-description').text();

        var index = compareList.findIndex(function(item) {
            return item.name === serviceName;
        });

        if (index !== -1) {
            compareList.splice(index, 1);
            $(this).removeClass('active');
            showNotification('Removed from comparison.', 'info');
        } else {
            if (compareList.length >= 3) {
                showNotification('You can compare up to 3 services.', 'warning');
                return;
            }
            compareList.push({
                name: serviceName,
                price: servicePrice,
                description: serviceDesc
            });
            $(this).addClass('active');
            showNotification('Added to comparison.', 'success');
        }

        updateCompareButton();
    });

    function updateCompareButton() {
        var btn = $('#compareServices');
        if (compareList.length > 0) {
            btn.show();
            btn.text('Compare (' + compareList.length + ')');
        } else {
            btn.hide();
        }
    }

    $('#compareServices').on('click', function() {
        if (compareList.length < 2) {
            showNotification('Select at least 2 services to compare.', 'warning');
            return;
        }

        var html = '<div class="modal-overlay"><div class="compare-popup"><h3>Compare Services</h3><div class="compare-grid">';

        compareList.forEach(function(service) {
            html += '<div class="compare-item">';
            html += '<h4>' + service.name + '</h4>';
            html += '<p>' + service.description + '</p>';
            html += '<div class="compare-price">R' + service.price.toLocaleString() + '</div>';
            html += '<a href="/contact?service=' + service.name.toLowerCase() + '" class="btn btn-sm btn-primary">Inquire</a>';
            html += '</div>';
        });

        html += '</div><div class="compare-actions"><button class="btn btn-outline-secondary" id="clearCompare">Clear Comparison</button> <button class="btn btn-secondary" id="closeCompare">Close</button></div></div></div>';

        var popup = $('<div class="modal-overlay">' + html + '</div>');
        $('body').append(popup);

        popup.find('#clearCompare').on('click', function() {
            compareList = [];
            $('.compare-service').removeClass('active');
            updateCompareButton();
            popup.remove();
            showNotification('Comparison cleared.', 'info');
        });

        popup.find('#closeCompare').on('click', function() {
            popup.remove();
        });

        popup.on('click', function(e) {
            if (e.target === this) {
                popup.remove();
            }
        });
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

    // ===== Initialize =====
    updateQuoteBadge();

    // ===== Add modal styles =====
    var style = `
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            padding: 20px;
        }
        .modal-overlay .quote-popup,
        .modal-overlay .compare-popup {
            background: #fff;
            border-radius: 12px;
            padding: 30px;
            max-width: 700px;
            width: 100%;
            max-height: 80vh;
            overflow-y: auto;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        .modal-overlay .compare-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .modal-overlay .compare-item {
            padding: 20px;
            border: 1px solid #eee;
            border-radius: 8px;
            text-align: center;
        }
        .modal-overlay .compare-price {
            font-size: 20px;
            font-weight: 700;
            color: #6c5ce7;
            margin: 10px 0;
        }
        .modal-overlay .quote-table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        .modal-overlay .quote-table th,
        .modal-overlay .quote-table td {
            padding: 10px;
            border-bottom: 1px solid #eee;
            text-align: left;
        }
        .modal-overlay .quote-table th {
            background: #f8f9fa;
            font-weight: 600;
        }
        .modal-overlay .qty-btn {
            background: #f0f0f0;
            border: none;
            width: 24px;
            height: 24px;
            border-radius: 4px;
            cursor: pointer;
        }
        .modal-overlay .qty-btn:hover {
            background: #6c5ce7;
            color: #fff;
        }
        .modal-overlay .remove-item {
            background: none;
            border: none;
            color: #e74c3c;
            cursor: pointer;
        }
        .modal-overlay .quote-actions {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
        .modal-overlay .compare-actions {
            display: flex;
            gap: 10px;
            margin-top: 20px;
            justify-content: center;
        }
        #quoteBadge {
            background: #e74c3c;
            color: #fff;
            border-radius: 50%;
            padding: 2px 8px;
            font-size: 12px;
            margin-left: 5px;
            display: none;
        }
        .compare-service.active {
            background: #6c5ce7;
            color: #fff;
            border-color: #6c5ce7;
        }
    `;
    $('<style>').html(style).appendTo('head');
});