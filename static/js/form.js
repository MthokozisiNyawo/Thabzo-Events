/**
 * THABZO EVENTS - Form JavaScript
 * Handles form validation, submission, and interactions
 */

$(document).ready(function() {

    // ===== Form Validation =====
    $('form[data-validate]').on('submit', function(e) {
        var $form = $(this);
        var isValid = true;

        // Clear previous errors
        $form.find('.is-invalid').removeClass('is-invalid');
        $form.find('.invalid-feedback').remove();

        // Validate required fields
        $form.find('[required]').each(function() {
            var $field = $(this);
            var value = $field.val().trim();

            if (!value) {
                markInvalid($field, 'This field is required.');
                isValid = false;
            } else {
                // Check field type
                var type = $field.attr('type');
                var name = $field.attr('name');

                if (type === 'email' && !isValidEmail(value)) {
                    markInvalid($field, 'Please enter a valid email address.');
                    isValid = false;
                }

                if (type === 'tel' && !isValidPhone(value)) {
                    markInvalid($field, 'Please enter a valid phone number.');
                    isValid = false;
                }

                if (name === 'event_type' && value === '') {
                    markInvalid($field, 'Please select an event type.');
                    isValid = false;
                }
            }
        });

        // Validate date fields
        $form.find('[type="date"]').each(function() {
            var $field = $(this);
            var value = $field.val();
            if (value) {
                var date = new Date(value);
                var today = new Date();
                today.setHours(0, 0, 0, 0);
                if (date < today) {
                    markInvalid($field, 'Date cannot be in the past.');
                    isValid = false;
                }
            }
        });

        // Validate password confirmation
        var password = $form.find('[name="password"]').val();
        var confirm = $form.find('[name="confirm_password"]').val();
        if (password || confirm) {
            if (password !== confirm) {
                markInvalid($form.find('[name="confirm_password"]'), 'Passwords do not match.');
                isValid = false;
            }
            if (password && password.length < 6) {
                markInvalid($form.find('[name="password"]'), 'Password must be at least 6 characters.');
                isValid = false;
            }
        }

        if (!isValid) {
            e.preventDefault();
            // Scroll to first error
            var firstError = $form.find('.is-invalid:first');
            if (firstError.length) {
                $('html, body').animate({
                    scrollTop: firstError.offset().top - 120
                }, 500);
                firstError.focus();
            }
        } else {
            // Show loading state
            var submitBtn = $form.find('[type="submit"]');
            submitBtn.html('<i class="fas fa-spinner fa-spin"></i> Processing...');
            submitBtn.prop('disabled', true);
        }
    });

    // ===== Mark field as invalid =====
    function markInvalid($field, message) {
        $field.addClass('is-invalid');
        var $feedback = $field.siblings('.invalid-feedback');
        if ($feedback.length) {
            $feedback.text(message);
        } else {
            $field.after('<div class="invalid-feedback">' + message + '</div>');
        }
    }

    // ===== Clear validation on input =====
    $('.form-control').on('input change', function() {
        var $field = $(this);
        $field.removeClass('is-invalid');
        $field.siblings('.invalid-feedback').remove();
    });

    // ===== Email validation =====
    function isValidEmail(email) {
        var re = /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
        return re.test(String(email).toLowerCase());
    }

    // ===== Phone validation =====
    function isValidPhone(phone) {
        var cleaned = phone.replace(/[\s\-\(\)]/g, '');
        var patterns = [
            /^0[6-8][0-9]{8}$/,
            /^\+27[6-8][0-9]{8}$/,
            /^27[6-8][0-9]{8}$/
        ];
        return patterns.some(function(pattern) {
            return pattern.test(cleaned);
        });
    }

    // ===== Auto-format phone numbers =====
    $('input[type="tel"]').on('input', function() {
        var $field = $(this);
        var value = $field.val().replace(/\D/g, '');

        if (value.length <= 3) {
            $field.val(value);
        } else if (value.length <= 6) {
            $field.val(value.substring(0, 3) + ' ' + value.substring(3));
        } else if (value.length <= 10) {
            $field.val(value.substring(0, 3) + ' ' + value.substring(3, 6) + ' ' + value.substring(6));
        } else {
            $field.val(value.substring(0, 3) + ' ' + value.substring(3, 6) + ' ' + value.substring(6, 10));
        }
    });

    // ===== Auto-fill service from URL =====
    var urlParams = new URLSearchParams(window.location.search);
    var service = urlParams.get('service');
    if (service) {
        var eventTypeMap = {
            'weddings': 'wedding',
            'wedding': 'wedding',
            'birthdays': 'birthday',
            'birthday': 'birthday',
            'corporate': 'corporate',
            'corporate-events': 'corporate',
            'baby-shower': 'baby-shower',
            'babyshower': 'baby-shower',
            'engagement': 'engagement',
            'anniversary': 'anniversary',
            'other': 'other'
        };

        var mappedValue = eventTypeMap[service] || service;
        $('#event_type').val(mappedValue);

        // Add visual feedback
        var $field = $('#event_type');
        $field.css('border-color', '#2ecc71');
        setTimeout(function() {
            $field.css('border-color', '');
        }, 3000);
    }

    // ===== Auto-fill from previous session =====
    if (localStorage.getItem('inquiryFormData')) {
        try {
            var savedData = JSON.parse(localStorage.getItem('inquiryFormData'));
            var $form = $('#inquiryForm');
            for (var key in savedData) {
                var $field = $form.find('[name="' + key + '"]');
                if ($field.length && $field.val() === '') {
                    $field.val(savedData[key]);
                }
            }
        } catch(e) {}
    }

    // ===== Save form data on input =====
    $('#inquiryForm .form-control').on('input change', function() {
        var formData = {};
        $('#inquiryForm .form-control').each(function() {
            var $field = $(this);
            var name = $field.attr('name');
            if (name) {
                formData[name] = $field.val();
            }
        });
        localStorage.setItem('inquiryFormData', JSON.stringify(formData));
    });

    // ===== Clear saved data on successful submit =====
    $(document).on('submit', '#inquiryForm', function() {
        localStorage.removeItem('inquiryFormData');
    });

    // ===== Character counter =====
    $('textarea[maxlength]').each(function() {
        var $field = $(this);
        var max = parseInt($field.attr('maxlength'));
        var $counter = $('<span class="char-counter">0/' + max + '</span>');
        $field.after($counter);

        $field.on('input', function() {
            var length = $(this).val().length;
            $counter.text(length + '/' + max);
            if (length > max * 0.9) {
                $counter.css('color', '#e74c3c');
            } else if (length > max * 0.7) {
                $counter.css('color', '#f39c12');
            } else {
                $counter.css('color', '#888');
            }
        });
    });

    // ===== AJAX Form Submission =====
    $('form[data-ajax]').on('submit', function(e) {
        e.preventDefault();
        var $form = $(this);
        var url = $form.attr('action') || window.location.href;
        var method = $form.attr('method') || 'POST';
        var data = $form.serialize();

        // Show loading
        var submitBtn = $form.find('[type="submit"]');
        var originalText = submitBtn.html();
        submitBtn.html('<i class="fas fa-spinner fa-spin"></i> Submitting...');
        submitBtn.prop('disabled', true);

        $.ajax({
            url: url,
            method: method,
            data: data,
            success: function(response) {
                if (response.success) {
                    showNotification(response.message || 'Form submitted successfully!', 'success');
                    $form.trigger('reset');
                    localStorage.removeItem('inquiryFormData');
                } else {
                    showNotification(response.message || 'An error occurred.', 'danger');
                }
                submitBtn.html(originalText);
                submitBtn.prop('disabled', false);
            },
            error: function(xhr) {
                var message = 'An error occurred. Please try again.';
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    message = xhr.responseJSON.message;
                }
                showNotification(message, 'danger');
                submitBtn.html(originalText);
                submitBtn.prop('disabled', false);
            }
        });
    });

    // ===== File Upload Preview =====
    $('input[type="file"]').on('change', function() {
        var $field = $(this);
        var file = $field[0].files[0];
        if (!file) return;

        if (file.type.startsWith('image/')) {
            var reader = new FileReader();
            reader.onload = function(e) {
                var preview = $field.siblings('.file-preview');
                if (!preview.length) {
                    preview = $('<div class="file-preview"></div>');
                    $field.after(preview);
                }
                preview.html('<img src="' + e.target.result + '" alt="Preview" style="max-width: 200px; max-height: 200px; border-radius: 8px; margin-top: 10px;">');
            };
            reader.readAsDataURL(file);
        }

        var fileName = $field.siblings('.file-name');
        if (!fileName.length) {
            fileName = $('<span class="file-name"></span>');
            $field.after(fileName);
        }
        fileName.text(file.name);
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

    // ===== Expose functions globally =====
    window.isValidEmail = isValidEmail;
    window.isValidPhone = isValidPhone;
    window.showNotification = showNotification;
});