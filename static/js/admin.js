/**
 * THABZO EVENTS - Admin JavaScript
 */

$(document).ready(function() {

    // ===== Sidebar Toggle =====
    $('#sidebarToggle, #topbarToggle').on('click', function() {
        $('#adminSidebar').toggleClass('open');
    });

    // Close sidebar on outside click (mobile)
    $(document).on('click', function(e) {
        if ($(window).width() <= 992) {
            if (!$(e.target).closest('#adminSidebar').length &&
                !$(e.target).closest('#sidebarToggle').length &&
                !$(e.target).closest('#topbarToggle').length) {
                $('#adminSidebar').removeClass('open');
            }
        }
    });

    // ===== Select All Checkbox =====
    $('#selectAll').on('change', function() {
        $('.inquiry-select, .item-select').prop('checked', $(this).prop('checked'));
        updateSelectedCount();
    });

    // Individual checkbox
    $('.inquiry-select, .item-select').on('change', function() {
        updateSelectedCount();
        $('#selectAll').prop('checked',
            $('.inquiry-select:checked, .item-select:checked').length ===
            $('.inquiry-select, .item-select').length
        );
    });

    function updateSelectedCount() {
        var count = $('.inquiry-select:checked, .item-select:checked').length;
        $('#selectedCount').text(count);
    }

    // ===== Alert Dismiss =====
    $('.alert-close').on('click', function() {
        $(this).closest('.alert').fadeOut(300);
    });

    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        $('.alert').fadeOut(500);
    }, 5000);

    // ===== Bulk Actions =====
    $('#bulkForm').on('submit', function(e) {
        var action = $('#bulkAction').val();
        var selected = $('.inquiry-select:checked, .item-select:checked').length;

        if (selected === 0) {
            e.preventDefault();
            showNotification('Please select at least one item.', 'warning');
            return;
        }

        if (!action) {
            e.preventDefault();
            showNotification('Please select an action.', 'warning');
            return;
        }

        if (action === 'delete' && !confirm('Are you sure you want to delete the selected items?')) {
            e.preventDefault();
        }
    });

    // ===== Delete Confirmation =====
    $('.delete-btn, .btn-delete').on('click', function(e) {
        if (!confirm('Are you sure you want to delete this item?')) {
            e.preventDefault();
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
                scrollTop: $('.is-invalid:first').offset().top - 150
            }, 500);
        }
    });

    // Remove invalid class on input
    $('.form-control').on('input', function() {
        $(this).removeClass('is-invalid');
    });

    // ===== Slug Generator =====
    $('#name').on('input', function() {
        var slug = $(this).val()
            .toLowerCase()
            .replace(/[^a-z0-9\s-]/g, '')
            .replace(/\s+/g, '-')
            .replace(/-+/g, '-');
        $('#slug').val(slug);
    });

    // ===== Image Preview =====
    $('input[type="file"]').on('change', function() {
        var file = this.files[0];
        if (file && file.type.startsWith('image/')) {
            var reader = new FileReader();
            reader.onload = function(e) {
                var preview = $('.current-image img');
                if (preview.length) {
                    preview.attr('src', e.target.result);
                } else {
                    $('.current-image').append(
                        '<img src="' + e.target.result + '" style="max-width: 300px; max-height: 200px; border-radius: 8px; margin-top: 10px;">'
                    );
                }
            };
            reader.readAsDataURL(file);
        }
    });

    // ===== Notification System =====
    function showNotification(message, type) {
        var types = {
            success: 'alert-success',
            warning: 'alert-warning',
            danger: 'alert-danger',
            info: 'alert-info'
        };

        var alertClass = types[type] || 'alert-info';
        var icon = {
            success: 'fa-check-circle',
            warning: 'fa-exclamation-triangle',
            danger: 'fa-exclamation-circle',
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

    // ===== Status Update =====
    $('.status-update').on('change', function() {
        var $this = $(this);
        var id = $this.data('id');
        var status = $this.val();

        $.ajax({
            url: '/admin/inquiry/' + id + '/update',
            method: 'POST',
            data: {
                status: status,
                csrf_token: $('input[name="csrf_token"]').val()
            },
            success: function(response) {
                showNotification('Status updated successfully.', 'success');
            },
            error: function() {
                showNotification('Failed to update status.', 'danger');
            }
        });
    });

    // ===== Toggle Switch =====
    $('.toggle-switch').on('change', function() {
        var $this = $(this);
        var id = $this.data('id');
        var type = $this.data('type');

        $.ajax({
            url: '/admin/' + type + '/' + id + '/toggle',
            method: 'POST',
            data: {
                csrf_token: $('input[name="csrf_token"]').val()
            },
            success: function(response) {
                showNotification(type + ' toggled successfully.', 'success');
                // Reload page to reflect changes
                setTimeout(function() {
                    location.reload();
                }, 1000);
            },
            error: function() {
                showNotification('Failed to toggle.', 'danger');
            }
        });
    });

    // ===== Filter Dropdown =====
    $('.filter-dropdown').on('change', function() {
        var url = new URL(window.location.href);
        url.searchParams.set('filter', $(this).val());
        window.location.href = url.toString();
    });

    // ===== Search Form =====
    $('.search-form').on('submit', function(e) {
        e.preventDefault();
        var query = $(this).find('input[name="search"]').val();
        var url = new URL(window.location.href);
        url.searchParams.set('search', query);
        window.location.href = url.toString();
    });

    // ===== Export Data =====
    $('.export-btn').on('click', function() {
        var type = $(this).data('type');
        var url = '/admin/export/' + type + '?' + window.location.search.substring(1);
        window.location.href = url;
    });

    // ===== Chart Resize =====
    function resizeCharts() {
        $('canvas').each(function() {
            if (this.chart) {
                this.chart.resize();
            }
        });
    }

    $(window).on('resize', function() {
        resizeCharts();
    });

    // ===== Keyboard Shortcuts =====
    $(document).on('keydown', function(e) {
        // Ctrl+S to save
        if (e.ctrlKey && e.key === 's') {
            e.preventDefault();
            $('form').submit();
        }
        // Esc to close modals
        if (e.key === 'Escape') {
            $('.modal, .lightbox').fadeOut(300);
        }
    });
});

// ===== Export functions =====
window.showNotification = function(message, type) {
    var types = {
        success: 'alert-success',
        warning: 'alert-warning',
        danger: 'alert-danger',
        info: 'alert-info'
    };

    var alertClass = types[type] || 'alert-info';
    var icon = {
        success: 'fa-check-circle',
        warning: 'fa-exclamation-triangle',
        danger: 'fa-exclamation-circle',
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
};