// Smooth scrolling for navigation links
document.querySelectorAll('.market-nav-menu a').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        const targetId = this.getAttribute('href');
        const targetSection = document.querySelector(targetId);
        
        if (targetSection) {
            const navHeight = document.querySelector('.market-navbar')?.offsetHeight || 0;
            const targetPosition = targetSection.offsetTop - navHeight;
            
            window.scrollTo({
                top: targetPosition,
                behavior: 'smooth'
            });
        }
    });
});

// CTA button smooth scroll
const heroCta = document.querySelector('.hero .cta-button');
if (heroCta) {
    heroCta.addEventListener('click', function() {
        const problemSection = document.querySelector('#problem');
        const navHeight = document.querySelector('.market-navbar')?.offsetHeight || 0;
        if (!problemSection) return;
        const targetPosition = problemSection.offsetTop - navHeight;
        
        window.scrollTo({
            top: targetPosition,
            behavior: 'smooth'
        });
    });
}

// Navbar scroll effect
let lastScroll = 0;
const navbar = document.querySelector('.market-navbar');

window.addEventListener('scroll', () => {
    const currentScroll = window.pageYOffset;
    
    // Add shadow on scroll
    if (currentScroll > 50) {
        navbar.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.2)';
    } else {
        navbar.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.1)';
    }
    
    lastScroll = currentScroll;
});

// Intersection Observer for animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -100px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Observe all cards and sections
const animateElements = document.querySelectorAll('.problem-card, .timing-card, .feature-card, .persona-card, .business-card, .roadmap-item, .traction-stat');

animateElements.forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(30px)';
    el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    observer.observe(el);
});

// Animate chart bars on scroll
const chartObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const bars = entry.target.querySelectorAll('.chart-bar');
            bars.forEach((bar, index) => {
                setTimeout(() => {
                    bar.style.opacity = '1';
                    bar.style.transform = 'scaleY(1)';
                }, index * 100);
            });
        }
    });
}, { threshold: 0.3 });

const chartContainer = document.querySelector('.chart-container');
if (chartContainer) {
    // Set initial state for chart bars
    document.querySelectorAll('.chart-bar').forEach(bar => {
        bar.style.opacity = '0';
        bar.style.transform = 'scaleY(0)';
        bar.style.transformOrigin = 'bottom';
        bar.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
    });
    
    chartObserver.observe(chartContainer);
}

// Animate market bars on scroll
const marketObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const bars = entry.target.querySelectorAll('.market-bar');
            bars.forEach((bar, index) => {
                setTimeout(() => {
                    bar.style.opacity = '1';
                    
                    // Trigger the width animation
                    const beforeElement = window.getComputedStyle(bar, '::before');
                    bar.classList.add('animated');
                }, index * 200);
            });
        }
    });
}, { threshold: 0.3 });

const marketVisual = document.querySelector('.market-visual');
if (marketVisual) {
    // Set initial state
    document.querySelectorAll('.market-bar').forEach(bar => {
        bar.style.opacity = '0';
        bar.style.transition = 'opacity 0.5s ease';
    });
    
    marketObserver.observe(marketVisual);
}

// Counter animation for statistics
function animateCounter(element, target, duration = 2000) {
    const start = 0;
    const increment = target / (duration / 16);
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            element.textContent = target + (element.dataset.suffix || '');
            clearInterval(timer);
        } else {
            element.textContent = Math.floor(current) + (element.dataset.suffix || '');
        }
    }, 16);
}

// Observe traction stats for counter animation
const statsObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting && !entry.target.classList.contains('counted')) {
            entry.target.classList.add('counted');
            const numberElement = entry.target.querySelector('.stat-number');
            const text = numberElement.textContent;
            const hasPercent = text.includes('%');
            const hasDash = text.includes('-');
            
            if (hasPercent) {
                const number = parseInt(text.replace('%', ''));
                numberElement.dataset.suffix = '%';
                animateCounter(numberElement, number);
            } else if (hasDash) {
                // For ranges like "60-65%", just show them without animation
                // (animation would be complex for ranges)
                numberElement.style.opacity = '1';
            } else {
                const number = parseInt(text);
                if (!isNaN(number)) {
                    animateCounter(numberElement, number);
                }
            }
        }
    });
}, { threshold: 0.5 });

document.querySelectorAll('.traction-stat').forEach(stat => {
    statsObserver.observe(stat);
});

// Market stats counter animation
const marketStatsObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting && !entry.target.classList.contains('counted')) {
            entry.target.classList.add('counted');
            
            // Animate the value numbers if they contain numeric data
            const valueElement = entry.target.querySelector('.stat-value');
            if (valueElement && valueElement.textContent.includes('Cr')) {
                valueElement.style.opacity = '0';
                setTimeout(() => {
                    valueElement.style.transition = 'opacity 0.8s ease';
                    valueElement.style.opacity = '1';
                }, 200);
            }
        }
    });
}, { threshold: 0.5 });

document.querySelectorAll('.market-stat').forEach(stat => {
    marketStatsObserver.observe(stat);
});

// Add active state to navigation based on scroll position
window.addEventListener('scroll', () => {
    const sections = document.querySelectorAll('.section[id]');
    const navLinks = document.querySelectorAll('.market-nav-menu a');
    
    let current = '';
    
    sections.forEach(section => {
        const sectionTop = section.offsetTop;
        const sectionHeight = section.clientHeight;
        const navHeight = navbar.offsetHeight;
        
        if (window.pageYOffset >= (sectionTop - navHeight - 100)) {
            current = section.getAttribute('id');
        }
    });
    
    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === `#${current}`) {
            link.classList.add('active');
        }
    });
});

// Add hover effect sound (optional - comment out if not needed)
// document.querySelectorAll('.problem-card, .timing-card, .feature-card').forEach(card => {
//     card.addEventListener('mouseenter', () => {
//         card.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
//     });
// });

// Roadmap items stagger animation
const roadmapObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const items = entry.target.querySelectorAll('.roadmap-item');
            items.forEach((item, index) => {
                setTimeout(() => {
                    item.style.opacity = '1';
                    item.style.transform = 'translateY(0)';
                }, index * 200);
            });
        }
    });
}, { threshold: 0.2 });

const roadmapTimeline = document.querySelector('.roadmap-timeline');
if (roadmapTimeline) {
    document.querySelectorAll('.roadmap-item').forEach(item => {
        item.style.opacity = '0';
        item.style.transform = 'translateY(30px)';
        item.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    });
    roadmapObserver.observe(roadmapTimeline);
}

// Table row highlight on hover
document.querySelectorAll('tbody tr').forEach(row => {
    row.addEventListener('mouseenter', function() {
        this.style.transform = 'scale(1.02)';
        this.style.transition = 'transform 0.2s ease';
    });
    
    row.addEventListener('mouseleave', function() {
        this.style.transform = 'scale(1)';
    });
});

// Parallax effect for hero section
window.addEventListener('scroll', () => {
    const scrolled = window.pageYOffset;
    const heroContent = document.querySelector('.hero-content');
    
    if (heroContent && scrolled < window.innerHeight) {
        heroContent.style.transform = `translateY(${scrolled * 0.5}px)`;
        heroContent.style.opacity = 1 - (scrolled / window.innerHeight);
    }
});

// Mobile menu toggle (for responsive design)
const createMobileMenu = () => {
    const navMenu = document.querySelector('.market-nav-menu');
    const navContainer = document.querySelector('.market-nav-container');
    if (!navMenu || !navContainer) return;
    if (window.innerWidth <= 768) {
        
        // Check if hamburger already exists
        if (!document.querySelector('.hamburger')) {
            const hamburger = document.createElement('div');
            hamburger.className = 'hamburger';
            hamburger.innerHTML = '☰';
            hamburger.style.cssText = `
                display: block;
                font-size: 1.8rem;
                color: white;
                cursor: pointer;
                padding: 0.5rem;
            `;
            
            hamburger.addEventListener('click', () => {
                navMenu.classList.toggle('active');
                if (navMenu.classList.contains('active')) {
                    navMenu.style.display = 'flex';
                    navMenu.style.flexDirection = 'column';
                    navMenu.style.position = 'absolute';
                    navMenu.style.top = '100%';
                    navMenu.style.left = '0';
                    navMenu.style.width = '100%';
                    navMenu.style.background = 'var(--primary-green)';
                    navMenu.style.padding = '1rem';
                    navMenu.style.gap = '1rem';
                } else {
                    navMenu.style.display = 'none';
                }
            });
            
            navContainer.appendChild(hamburger);
        }
    }
};

// Initialize mobile menu on load and resize
window.addEventListener('load', createMobileMenu);
window.addEventListener('resize', createMobileMenu);

// CTA section button interaction
const ctaButtonLarge = document.querySelector('.cta-button-large');
if (ctaButtonLarge) {
    ctaButtonLarge.addEventListener('click', function() {
        alert('Thank you for your interest! Please contact us at contact@agrorent.com');
    });
}

// Add loading animation
window.addEventListener('load', () => {
    document.body.style.opacity = '0';
    setTimeout(() => {
        document.body.style.transition = 'opacity 0.5s ease';
        document.body.style.opacity = '1';
    }, 100);
});

console.log('AgroRent Pitch Deck Loaded Successfully! 🌾');