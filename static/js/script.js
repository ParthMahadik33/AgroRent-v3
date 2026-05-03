// DOM Content Loaded Event
document.addEventListener('DOMContentLoaded', function () {
    initSmoothScrolling();
    initScrollAnimations();
    initVideoHandling();
    initNavbar();
    initProfileDropdown();
    initFlashMessages();
});

// Smooth scrolling for anchor links
function initSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href !== '#' && href.length > 1) {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });
}

// Dropdown functionality
function initProfileDropdown() {
    // Defines dropdown configuration: {btnId, menuId}
    const dropdowns = [
        { btnId: 'profile-btn', menuId: 'dropdown-menu' },
        { btnId: 'language-btn', menuId: 'language-menu' },
        { btnId: 'mechanic-btn', menuId: 'mechanic-menu' }
    ];

    // Initialize each dropdown
    dropdowns.forEach(config => {
        const btn = document.getElementById(config.btnId);
        const menu = document.getElementById(config.menuId);

        if (btn && menu) {
            // Toggle on click
            btn.addEventListener('click', function (e) {
                e.stopPropagation();

                // Toggle current
                const isOpening = !menu.classList.contains('active');
                menu.classList.toggle('active');
                btn.classList.toggle('active');

                // Close all others if opening
                if (isOpening) {
                    dropdowns.forEach(other => {
                        if (other.btnId !== config.btnId) {
                            const otherBtn = document.getElementById(other.btnId);
                            const otherMenu = document.getElementById(other.menuId);
                            if (otherBtn && otherMenu) {
                                otherMenu.classList.remove('active');
                                otherBtn.classList.remove('active');
                            }
                        }
                    });
                }
            });

            // Prevent closing when clicking inside menu
            menu.addEventListener('click', function (e) {
                e.stopPropagation();
            });
        }
    });

    // Close all when clicking outside
    document.addEventListener('click', function (e) {
        dropdowns.forEach(config => {
            const btn = document.getElementById(config.btnId);
            const menu = document.getElementById(config.menuId);
            if (btn && menu && !btn.contains(e.target) && !menu.contains(e.target)) {
                menu.classList.remove('active');
                btn.classList.remove('active');
            }
        });
    });
}

// Enhanced Navbar functionality
function initNavbar() {
    const navToggle = document.getElementById('nav-toggle');
    const navMenu = document.getElementById('nav-menu');
    const navbar = document.querySelector('.navbar');
    const navLinks = document.querySelectorAll('.nav-link');

    // Mobile menu toggle
    if (navToggle && navMenu) {
        navToggle.addEventListener('click', () => {
            navMenu.classList.toggle('active');
            navToggle.classList.toggle('active');
        });

        // Close mobile menu when clicking on links
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                navMenu.classList.remove('active');
                navToggle.classList.remove('active');
            });
        });

        // Close mobile menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!navbar.contains(e.target)) {
                navMenu.classList.remove('active');
                navToggle.classList.remove('active');
            }
        });
    }

    // Enhanced navbar scroll effect
    if (navbar) {
        let lastScrollY = window.scrollY;

        window.addEventListener('scroll', debounce(() => {
            const currentScrollY = window.scrollY;

            if (currentScrollY > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }

            // Hide/show navbar on scroll (optional - disable if you don't want this)
            if (currentScrollY > lastScrollY && currentScrollY > 200) {
                navbar.style.transform = 'translateY(-100%)';
            } else {
                navbar.style.transform = 'translateY(0)';
            }

            lastScrollY = currentScrollY;
        }, 10));
    }

    // Enhanced active link highlighting
    function updateActiveLink() {
        const sections = document.querySelectorAll('section');
        const scrollPos = window.scrollY + 150;

        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.offsetHeight;
            const sectionId = section.getAttribute('id') || 'home';

            if (scrollPos >= sectionTop && scrollPos < sectionTop + sectionHeight) {
                navLinks.forEach(link => {
                    link.classList.remove('active');
                    const href = link.getAttribute('href');
                    if (href === `#${sectionId}` || (sectionId === 'home' && href === '#home')) {
                        link.classList.add('active');
                    }
                });
            }
        });

        // Handle hero section
        if (scrollPos < 100) {
            navLinks.forEach(link => {
                link.classList.remove('active');
                if (link.getAttribute('href') === '#home') {
                    link.classList.add('active');
                }
            });
        }
    }

    window.addEventListener('scroll', debounce(updateActiveLink, 50));
    updateActiveLink(); // Initialize on load
}

// Fade in animation on scroll
function initScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, observerOptions);

    // Observe all fade-in elements
    document.querySelectorAll('.fade-in').forEach(el => {
        observer.observe(el);
    });
}

// Video handling and optimization
function initVideoHandling() {
    const video = document.querySelector('video');
    const heroSection = document.querySelector('.hero');

    if (!video || !heroSection) return;

    // Handle video loading error
    video.addEventListener('error', function () {
        console.warn('Video failed to load, using fallback background');
        // Fallback: Create a gradient background if video fails
        const videoBackground = document.querySelector('.video-background');
        if (videoBackground) {
            videoBackground.style.background = 'linear-gradient(45deg, #2E8B57, #228B22)';
            this.style.display = 'none';
        }
    });

    // Performance optimization: pause video when not in view
    const heroObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                video.play().catch(e => {
                    console.warn('Video play failed:', e);
                });
            } else {
                video.pause();
            }
        });
    }, { threshold: 0.5 });

    heroObserver.observe(heroSection);

    // Ensure video is muted for autoplay compliance
    video.muted = true;
    video.setAttribute('muted', '');
    video.setAttribute('playsinline', '');
}

// Flash messages auto-dismiss
function initFlashMessages() {
    const alerts = document.querySelectorAll('.alert');

    alerts.forEach(alert => {
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            alert.style.animation = 'slideOut 0.3s ease forwards';
            setTimeout(() => {
                alert.remove();
            }, 300);
        }, 5000);
    });
}

// Add slide out animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Form validation for auth pages
function initFormValidation() {
    const forms = document.querySelectorAll('.auth-form');

    forms.forEach(form => {
        form.addEventListener('submit', function (e) {
            const password = form.querySelector('input[name="password"]');
            const confirmPassword = form.querySelector('input[name="confirm_password"]');

            if (confirmPassword && password.value !== confirmPassword.value) {
                e.preventDefault();
                alert('Passwords do not match!');
                confirmPassword.focus();
                return false;
            }

            if (password && password.value.length < 6) {
                e.preventDefault();
                alert('Password must be at least 6 characters long!');
                password.focus();
                return false;
            }
        });
    });
}

// Initialize form validation
document.addEventListener('DOMContentLoaded', initFormValidation);

// Error handling for missing elements
function handleMissingElements() {
    const requiredElements = ['.hero', '.categories-grid'];

    requiredElements.forEach(selector => {
        const element = document.querySelector(selector);
        if (!element) {
            console.warn(`Optional element not found: ${selector}`);
        }
    });
}

// Call error handling on load
window.addEventListener('load', handleMissingElements);