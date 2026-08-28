// THABZO EVENTS - Navbar JavaScript
// Version 6.0

document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu toggle
    const menuToggle = document.querySelector('.menu-toggle, .navbar-toggler');
    const navMenu = document.querySelector('.nav-menu, .navbar-collapse');

    if (menuToggle && navMenu) {
        menuToggle.addEventListener('click', function() {
            navMenu.classList.toggle('active');
            navMenu.classList.toggle('show');
            menuToggle.classList.toggle('active');
        });
    }

    // Dropdown toggle for mobile
    const dropdowns = document.querySelectorAll('.dropdown-toggle, .nav-item.dropdown > a');
    dropdowns.forEach(function(dropdown) {
        dropdown.addEventListener('click', function(e) {
            if (window.innerWidth <= 768) {
                e.preventDefault();
                const parent = this.parentElement;
                const menu = parent.querySelector('.dropdown-menu');
                if (menu) {
                    menu.classList.toggle('show');
                }
            }
        });
    });

    // Navbar scroll effect
    const navbar = document.querySelector('.navbar, .main-nav');
    if (navbar) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        });
    }

    // Active link highlighting
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link, .nav-menu a');
    navLinks.forEach(function(link) {
        const href = link.getAttribute('href');
        if (href && currentPath === href) {
            link.classList.add('active');
        }
        // For parent dropdowns
        if (href && currentPath.startsWith(href) && href !== '/') {
            link.classList.add('active');
            const parent = link.closest('.dropdown');
            if (parent) {
                const toggle = parent.querySelector('.dropdown-toggle');
                if (toggle) {
                    toggle.classList.add('active');
                }
            }
        }
    });

    // Close menu when clicking outside
    document.addEventListener('click', function(e) {
        if (navMenu && navMenu.classList.contains('active')) {
            if (!navMenu.contains(e.target) && !menuToggle.contains(e.target)) {
                navMenu.classList.remove('active');
                navMenu.classList.remove('show');
                if (menuToggle) {
                    menuToggle.classList.remove('active');
                }
            }
        }
    });

    // Close menu on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && navMenu && navMenu.classList.contains('active')) {
            navMenu.classList.remove('active');
            navMenu.classList.remove('show');
            if (menuToggle) {
                menuToggle.classList.remove('active');
            }
        }
    });

    // Handle window resize
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768 && navMenu) {
            navMenu.classList.remove('active');
            navMenu.classList.remove('show');
            if (menuToggle) {
                menuToggle.classList.remove('active');
            }
        }
    });

    console.log('THABZO EVENTS - Navbar initialized');
});