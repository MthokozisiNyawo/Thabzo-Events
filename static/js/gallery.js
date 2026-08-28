/**
 * THABZO EVENTS - Gallery JavaScript
 * Handles gallery filtering, lightbox, and masonry layout
 */

$(document).ready(function() {

    // ===== Gallery Filtering =====
    $('.gallery-filter .filter-btn').on('click', function() {
        var filter = $(this).data('filter');

        // Update active button
        $('.gallery-filter .filter-btn').removeClass('active');
        $(this).addClass('active');

        // Filter items
        $('.gallery-item').each(function() {
            var $item = $(this);
            if (filter === 'all' || $item.data('category') === filter) {
                $item.show();
                // Re-animate
                setTimeout(function() {
                    $item.addClass('fade-in');
                }, 100);
            } else {
                $item.hide();
                $item.removeClass('fade-in');
            }
        });

        // Rebuild masonry layout
        if (typeof masonryGrid !== 'undefined') {
            masonryGrid.masonry('layout');
        }

        // Update URL with filter parameter
        var url = new URL(window.location.href);
        if (filter !== 'all') {
            url.searchParams.set('category', filter);
        } else {
            url.searchParams.delete('category');
        }
        window.history.pushState({}, '', url);
    });

    // ===== Load filter from URL =====
    var urlParams = new URLSearchParams(window.location.search);
    var category = urlParams.get('category');
    if (category) {
        $('.gallery-filter .filter-btn').each(function() {
            if ($(this).data('filter') === category) {
                $(this).trigger('click');
            }
        });
    }

    // ===== Lightbox =====
    var lightbox = $('#lightbox');
    var lightboxImg = $('#lightbox-img');
    var lightboxCaption = $('#lightbox-caption');

    // Open lightbox
    $(document).on('click', '.gallery-zoom, .gallery-item img', function(e) {
        e.preventDefault();

        var $this = $(this);
        var imgSrc = $this.attr('href') || $this.attr('src');
        var title = $this.closest('.gallery-item').find('.gallery-info h4').text();
        var description = $this.closest('.gallery-item').find('.gallery-info p').text();

        lightboxImg.attr('src', imgSrc);
        lightboxCaption.text(title || description || '');
        lightbox.fadeIn(300);

        // Prevent body scroll
        $('body').addClass('lightbox-open');
    });

    // Close lightbox
    $('.lightbox-close, .lightbox-overlay').on('click', function() {
        closeLightbox();
    });

    // Close with Escape key
    $(document).on('keydown', function(e) {
        if (e.key === 'Escape' && lightbox.is(':visible')) {
            closeLightbox();
        }
    });

    // Close with clicking on background
    lightbox.on('click', function(e) {
        if (e.target === this) {
            closeLightbox();
        }
    });

    function closeLightbox() {
        lightbox.fadeOut(300);
        $('body').removeClass('lightbox-open');
    }

    // ===== Lightbox Navigation =====
    var currentImageIndex = 0;
    var galleryItems = [];

    function getGalleryItems() {
        galleryItems = [];
        $('.gallery-item:visible').each(function() {
            var img = $(this).find('.gallery-zoom');
            galleryItems.push({
                src: img.attr('href') || img.attr('src'),
                title: $(this).find('.gallery-info h4').text(),
                description: $(this).find('.gallery-info p').text()
            });
        });
    }

    $(document).on('click', '.lightbox-next', function(e) {
        e.stopPropagation();
        getGalleryItems();
        currentImageIndex = (currentImageIndex + 1) % galleryItems.length;
        updateLightboxImage(currentImageIndex);
    });

    $(document).on('click', '.lightbox-prev', function(e) {
        e.stopPropagation();
        getGalleryItems();
        currentImageIndex = (currentImageIndex - 1 + galleryItems.length) % galleryItems.length;
        updateLightboxImage(currentImageIndex);
    });

    function updateLightboxImage(index) {
        var item = galleryItems[index];
        if (item) {
            lightboxImg.attr('src', item.src);
            lightboxCaption.text(item.title || item.description || '');
        }
    }

    // ===== Keyboard navigation in lightbox =====
    $(document).on('keydown', function(e) {
        if (!lightbox.is(':visible')) return;

        if (e.key === 'ArrowRight') {
            $('.lightbox-next').trigger('click');
        } else if (e.key === 'ArrowLeft') {
            $('.lightbox-prev').trigger('click');
        }
    });

    // ===== Masonry Gallery Layout =====
    function initMasonry() {
        if (typeof Masonry !== 'undefined') {
            var grid = $('.gallery-grid');
            if (grid.length && !grid.hasClass('masonry-initialized')) {
                masonryGrid = new Masonry(grid[0], {
                    itemSelector: '.gallery-item',
                    columnWidth: '.gallery-item',
                    gutter: 20,
                    fitWidth: true,
                    transitionDuration: '0.3s'
                });
                grid.addClass('masonry-initialized');

                // Images loaded
                imagesLoaded(grid[0], function() {
                    masonryGrid.layout();
                });
            }
        }
    }

    // ===== Load More Gallery Images =====
    var loadMoreBtn = $('#loadMoreGallery');
    var currentPage = 1;
    var loading = false;

    loadMoreBtn.on('click', function() {
        if (loading) return;
        loading = true;
        loadMoreBtn.text('Loading...');
        loadMoreBtn.prop('disabled', true);

        var category = $('.gallery-filter .filter-btn.active').data('filter') || 'all';

        $.ajax({
            url: '/gallery/load-more',
            method: 'GET',
            data: {
                page: currentPage + 1,
                category: category
            },
            success: function(response) {
                if (response.html) {
                    $('.gallery-grid').append(response.html);
                    currentPage = response.page;

                    // Init masonry for new items
                    if (typeof Masonry !== 'undefined') {
                        var grid = $('.gallery-grid');
                        if (grid.hasClass('masonry-initialized')) {
                            masonryGrid.appended($(response.html));
                            masonryGrid.layout();
                        }
                    }

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
                showNotification('Failed to load more images.', 'danger');
            }
        });
    });

    // ===== Gallery Search =====
    var searchInput = $('#gallerySearch');
    var searchTimeout;

    searchInput.on('input', function() {
        clearTimeout(searchTimeout);
        var query = $(this).val().toLowerCase().trim();

        searchTimeout = setTimeout(function() {
            $('.gallery-item').each(function() {
                var $item = $(this);
                var title = $item.find('.gallery-info h4').text().toLowerCase();
                var desc = $item.find('.gallery-info p').text().toLowerCase();
                var category = $item.data('category').toLowerCase();

                var match = title.includes(query) || desc.includes(query) || category.includes(query);
                $item.toggle(match);

                if (match) {
                    $item.addClass('fade-in');
                } else {
                    $item.removeClass('fade-in');
                }
            });

            // Update masonry
            if (typeof masonryGrid !== 'undefined') {
                masonryGrid.layout();
            }
        }, 300);
    });

    // ===== Fullscreen Mode =====
    $(document).on('click', '.lightbox-fullscreen', function(e) {
        e.stopPropagation();
        var elem = lightbox[0];
        if (elem.requestFullscreen) {
            elem.requestFullscreen();
        } else if (elem.webkitRequestFullscreen) {
            elem.webkitRequestFullscreen();
        } else if (elem.msRequestFullscreen) {
            elem.msRequestFullscreen();
        }
    });

    // ===== Download Image =====
    $(document).on('click', '.lightbox-download', function(e) {
        e.stopPropagation();
        var src = lightboxImg.attr('src');
        var link = document.createElement('a');
        link.download = src.split('/').pop();
        link.href = src;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });

    // ===== Share Image =====
    $(document).on('click', '.lightbox-share', function(e) {
        e.stopPropagation();
        var src = lightboxImg.attr('src');
        var title = lightboxCaption.text() || 'THABZO EVENTS Gallery';

        if (navigator.share) {
            navigator.share({
                title: title,
                text: 'Check out this beautiful decoration from THABZO EVENTS!',
                url: window.location.origin + src
            }).catch(function() {});
        } else {
            // Fallback - copy URL
            var url = window.location.origin + src;
            navigator.clipboard.writeText(url).then(function() {
                showNotification('Image URL copied to clipboard!', 'success');
            });
        }
    });

    // ===== Initialize =====
    initMasonry();

    // ===== Helper Functions =====
    function showNotification(message, type) {
        var alertClass = {
            success: 'alert-success',
            danger: 'alert-danger',
            warning: 'alert-warning',
            info: 'alert-info'
        }[type] || 'alert-info';

        var html = '<div class="alert ' + alertClass + ' alert-dismissible fade show" style="position: fixed; top: 20px; right: 20px; z-index: 9999; max-width: 400px; box-shadow: 0 4px 20px rgba(0,0,0,0.15);">' +
            '<i class="fas fa-' + (type === 'success' ? 'check-circle' : 'exclamation-circle') + '"></i> ' + message +
            '<button type="button" class="alert-close" data-dismiss="alert">&times;</button>' +
            '</div>';

        $('body').append(html);
        setTimeout(function() {
            $('.alert').fadeOut(500, function() {
                $(this).remove();
            });
        }, 5000);
    }
});

// ===== Lightbox HTML Structure =====
// This should be in the HTML but we ensure it exists
$(document).ready(function() {
    if ($('#lightbox').length === 0) {
        var lightboxHTML = `
            <div id="lightbox" class="lightbox" style="display:none;">
                <div class="lightbox-overlay"></div>
                <button class="lightbox-close" aria-label="Close">&times;</button>
                <button class="lightbox-prev" aria-label="Previous"><i class="fas fa-chevron-left"></i></button>
                <button class="lightbox-next" aria-label="Next"><i class="fas fa-chevron-right"></i></button>
                <div class="lightbox-content">
                    <img id="lightbox-img" src="" alt="Gallery image">
                    <div id="lightbox-caption"></div>
                </div>
                <div class="lightbox-toolbar">
                    <button class="lightbox-fullscreen" aria-label="Fullscreen"><i class="fas fa-expand"></i></button>
                    <button class="lightbox-download" aria-label="Download"><i class="fas fa-download"></i></button>
                    <button class="lightbox-share" aria-label="Share"><i class="fas fa-share-alt"></i></button>
                </div>
            </div>
        `;
        $('body').append(lightboxHTML);
    }
});