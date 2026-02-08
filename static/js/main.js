// ============================================
// MODALY WEBSITE - SINGLE THEME SYSTEM
// Dark Theme Removed - Company Branding Only
// #1e1e1e Background + #7c3aed Purple
// v3.0.0
// ============================================

(function() {
    'use strict';

    // ============================================
    // NAVBAR AUTO-HIDE/SHOW ON SCROLL
    // ============================================

    const NavbarManager = {
        init() {
            this.navbar = document.querySelector('.navbar');
            if (!this.navbar) return;

            this.lastScrollTop = 0;
            this.scrollThreshold = 5;
            this.setupScrollEffect();
        },

        setupScrollEffect() {
            let ticking = false;
            
            window.addEventListener('scroll', () => {
                if (!ticking) {
                    window.requestAnimationFrame(() => {
                        this.handleScroll();
                        ticking = false;
                    });
                    ticking = true;
                }
            });
        },

        handleScroll() {
            const currentScroll = window.pageYOffset || document.documentElement.scrollTop;
            
            // Add scrolled class when scrolled past threshold
            if (currentScroll > 50) {
                this.navbar.classList.add('scrolled');
            } else {
                this.navbar.classList.remove('scrolled');
            }
            
            // Don't hide navbar at the very top of the page
            if (currentScroll <= 0) {
                this.navbar.classList.remove('navbar-hidden');
                this.navbar.classList.add('navbar-visible');
                this.lastScrollTop = currentScroll;
                return;
            }
            
            // Check scroll direction
            if (Math.abs(currentScroll - this.lastScrollTop) < this.scrollThreshold) {
                return;
            }
            
            if (currentScroll > this.lastScrollTop && currentScroll > 100) {
                // Scrolling down - hide navbar
                this.navbar.classList.remove('navbar-visible');
                this.navbar.classList.add('navbar-hidden');
            } else {
                // Scrolling up - show navbar
                this.navbar.classList.remove('navbar-hidden');
                this.navbar.classList.add('navbar-visible');
            }
            
            this.lastScrollTop = currentScroll;
        }
    };

    // ============================================
    // ALERT AUTO-DISMISS
    // ============================================

    const AlertManager = {
        DISMISS_DELAY: 5000, // 5 seconds

        init() {
            this.setupAutoDismiss();
        },

        setupAutoDismiss() {
            const alerts = document.querySelectorAll('.alert');
            
            alerts.forEach(alert => {
                setTimeout(() => {
                    if (typeof bootstrap !== 'undefined' && bootstrap.Alert) {
                        const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                        bsAlert.close();
                    }
                }, this.DISMISS_DELAY);
            });
        }
    };

    // ============================================
    // SMOOTH SCROLLING
    // ============================================

    const SmoothScroll = {
        init() {
            this.setupAnchorLinks();
        },

        setupAnchorLinks() {
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {
                anchor.addEventListener('click', function(e) {
                    const href = this.getAttribute('href');
                    
                    // Skip if href is just "#"
                    if (href === '#' || href === '#!') return;
                    
                    const target = document.querySelector(href);
                    if (target) {
                        e.preventDefault();
                        const offsetTop = target.offsetTop - 80; // Account for fixed navbar
                        
                        window.scrollTo({
                            top: offsetTop,
                            behavior: 'smooth'
                        });

                        // Update URL without triggering scroll
                        history.pushState(null, null, href);
                    }
                });
            });
        }
    };

    // ============================================
    // FORM VALIDATION ENHANCEMENT
    // ============================================

    const FormValidator = {
        init() {
            this.setupBootstrapValidation();
        },

        setupBootstrapValidation() {
            const forms = document.querySelectorAll('.needs-validation');
            
            forms.forEach(form => {
                form.addEventListener('submit', function(event) {
                    if (!form.checkValidity()) {
                        event.preventDefault();
                        event.stopPropagation();
                    }
                    
                    form.classList.add('was-validated');
                }, false);
            });
        }
    };

    // ============================================
    // MOBILE MENU HANDLER
    // ============================================

    const MobileMenuManager = {
        init() {
            this.setupMobileMenuClose();
        },

        setupMobileMenuClose() {
            const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
            const navbarCollapse = document.querySelector('.navbar-collapse');
            
            if (!navbarCollapse) return;
            
            navLinks.forEach(link => {
                link.addEventListener('click', () => {
                    if (window.innerWidth < 992) {
                        if (typeof bootstrap !== 'undefined' && bootstrap.Collapse) {
                            const bsCollapse = bootstrap.Collapse.getInstance(navbarCollapse);
                            if (bsCollapse) {
                                bsCollapse.hide();
                            }
                        }
                    }
                });
            });
        }
    };

    // ============================================
    // DONATION AMOUNT SELECTOR
    // ============================================

    const DonationManager = {
        init() {
            this.setupAmountButtons();
        },

        setupAmountButtons() {
            const amountButtons = document.querySelectorAll('.donation-amount-btn');
            const customAmountInput = document.querySelector('#custom_amount');
            const hiddenAmountInput = document.querySelector('#amount');
            
            if (!amountButtons.length) return;
            
            amountButtons.forEach(button => {
                button.addEventListener('click', function() {
                    // Remove active class from all buttons
                    amountButtons.forEach(btn => btn.classList.remove('active'));
                    
                    // Add active class to clicked button
                    this.classList.add('active');
                    
                    // Set the amount
                    const amount = this.getAttribute('data-amount');
                    if (hiddenAmountInput) {
                        hiddenAmountInput.value = amount;
                    }
                    
                    // Clear custom amount
                    if (customAmountInput) {
                        customAmountInput.value = '';
                    }
                });
            });

            // Handle custom amount input
            if (customAmountInput) {
                customAmountInput.addEventListener('input', function() {
                    // Remove active class from all preset buttons
                    amountButtons.forEach(btn => btn.classList.remove('active'));
                    
                    // Update hidden field
                    if (hiddenAmountInput) {
                        hiddenAmountInput.value = this.value;
                    }
                });
            }
        }
    };

    // ============================================
    // IMAGE LAZY LOADING
    // ============================================

    const ImageLazyLoader = {
        init() {
            if ('loading' in HTMLImageElement.prototype) {
                // Native lazy loading supported
                const images = document.querySelectorAll('img[loading="lazy"]');
                images.forEach(img => {
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                    }
                });
            } else {
                // Fallback for older browsers
                this.loadPolyfill();
            }
        },

        loadPolyfill() {
            const script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/lazysizes/5.3.2/lazysizes.min.js';
            document.body.appendChild(script);
        }
    };

    // ============================================
    // ANALYTICS (Optional)
    // ============================================

    const Analytics = {
        init() {
            this.trackDonations();
            this.trackFormSubmissions();
        },

        trackDonations() {
            const donationForm = document.querySelector('form[action*="donate"]');
            
            if (donationForm) {
                donationForm.addEventListener('submit', function() {
                    console.log('Donation form submitted');
                    
                    // Send to analytics if configured
                    if (typeof gtag !== 'undefined') {
                        gtag('event', 'begin_donation');
                    }
                });
            }
        },

        trackFormSubmissions() {
            const contactForm = document.querySelector('form[action*="contact"]');
            
            if (contactForm) {
                contactForm.addEventListener('submit', function() {
                    console.log('Contact form submitted');
                    
                    if (typeof gtag !== 'undefined') {
                        gtag('event', 'contact_form_submit');
                    }
                });
            }
        }
    };

    // ============================================
    // ACCESSIBILITY ENHANCEMENTS
    // ============================================

    const A11y = {
        init() {
            this.setupKeyboardNavigation();
        },

        setupKeyboardNavigation() {
            // Allow escape key to close mobile menu
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    const navbarCollapse = document.querySelector('.navbar-collapse.show');
                    if (navbarCollapse && typeof bootstrap !== 'undefined' && bootstrap.Collapse) {
                        const bsCollapse = bootstrap.Collapse.getInstance(navbarCollapse);
                        if (bsCollapse) {
                            bsCollapse.hide();
                        }
                    }
                    
                    // Close admin sidebar on mobile
                    const adminSidebar = document.querySelector('.admin-sidebar.show');
                    if (adminSidebar) {
                        adminSidebar.classList.remove('show');
                        const overlay = document.querySelector('.admin-overlay.show');
                        if (overlay) {
                            overlay.classList.remove('show');
                        }
                    }
                }
            });
        }
    };

    // ============================================
    // PERFORMANCE MONITORING
    // ============================================

    const Performance = {
        init() {
            this.logLoadTime();
        },

        logLoadTime() {
            window.addEventListener('load', () => {
                if (window.performance && window.performance.timing) {
                    const loadTime = window.performance.timing.loadEventEnd - 
                                   window.performance.timing.navigationStart;
                    
                    console.log(`✅ Page loaded in ${loadTime}ms`);
                    console.log('🎨 Single theme system active (#1e1e1e + #7c3aed)');
                }
            });
        }
    };

    // ============================================
    // INITIALIZATION
    // ============================================

    function init() {
        console.log('🚀 Modaly Website v3.0.0 - Single Theme System');
        
        // Core features
        NavbarManager.init();
        AlertManager.init();
        SmoothScroll.init();
        FormValidator.init();
        MobileMenuManager.init();
        
        // Feature-specific
        DonationManager.init();
        ImageLazyLoader.init();
        
        // Enhancements
        Analytics.init();
        A11y.init();
        Performance.init();

        console.log('✨ All systems initialized');
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();