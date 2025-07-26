/**
 * home.js
 * JavaScript for the GT7 Tuning App home page
 */

document.addEventListener('DOMContentLoaded', function() {
    // Animate feature cards on scroll
    const featureCards = document.querySelectorAll('.card-hover');
    
    if (featureCards.length > 0) {
        // Add initial hidden state if we're using animation
        featureCards.forEach(card => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        });
        
        // Function to check if an element is in viewport
        const isInViewport = (elem) => {
            const bounding = elem.getBoundingClientRect();
            return (
                bounding.top >= 0 &&
                bounding.bottom <= (window.innerHeight || document.documentElement.clientHeight)
            );
        };
        
        // Function to handle scroll animation
        const handleScroll = () => {
            featureCards.forEach(card => {
                if (isInViewport(card)) {
                    setTimeout(() => {
                        card.style.opacity = '1';
                        card.style.transform = 'translateY(0)';
                    }, 100 * Array.from(featureCards).indexOf(card)); // Staggered animation
                }
            });
        };
        
        // Initial check and add scroll listener
        handleScroll();
        window.addEventListener('scroll', handleScroll);
    }
    
    // Add click handlers for quick action buttons
    const createSetupBtn = document.querySelector('.btn-primary[href*="calculate_springs"]');
    if (createSetupBtn) {
        createSetupBtn.addEventListener('click', function() {
            // Optional pre-loading animation
            showToast('Loading Calculator', 'Opening the Spring Rate Calculator...', 'info');
        });
    }
    
    // Check for returning users (session storage)
    const isReturningUser = sessionStorage.getItem('gt7_returning_user');
    if (!isReturningUser) {
        // First visit in this session, show welcome message
        setTimeout(() => {
            showToast('Welcome to GT7 Tuning App', 'Create professional racing setups for Gran Turismo 7', 'info', 5000);
            sessionStorage.setItem('gt7_returning_user', 'true');
        }, 1000);
    }
});

/**
 * Animate the step-by-step guide
 */
function animateGuideSteps() {
    const guideSteps = document.querySelectorAll('.guide-steps li');
    
    if (guideSteps.length === 0) return;
    
    guideSteps.forEach((step, index) => {
        // Set initial state
        step.style.opacity = '0';
        step.style.transform = 'translateX(-20px)';
        step.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        
        // Animate steps in sequence
        setTimeout(() => {
            step.style.opacity = '1';
            step.style.transform = 'translateX(0)';
        }, 300 * index); // Staggered timing
    });
}

// Trigger the animation when the page is loaded
window.addEventListener('load', animateGuideSteps);