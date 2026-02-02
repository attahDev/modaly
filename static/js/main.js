/**
 * Modaly - Main JavaScript
 * Theme toggle, animations, and interactions
 */

(function() {
    'use strict';

    // Declare bootstrap variable
    const bootstrap = window.bootstrap;

    // ==========================================================================
    // Theme Management
    // ==========================================================================
    
    const ThemeManager = {
        STORAGE_KEY: 'modaly-theme',
        DARK: 'dark',
        LIGHT: 'light',

        init() {
            this.applyStoredTheme();
            this.bindToggle();
        },

        getStoredTheme() {
            return localStorage.getItem(this.STORAGE_KEY);
        },

        getSystemTheme() {
            return window.matchMedia('(prefers-color-scheme: dark)').matches 
                ? this.DARK 
                : this.LIGHT;
        },

        applyStoredTheme() {
            const storedTheme = this.getStoredTheme();
            const theme = storedTheme || this.getSystemTheme();
            this.setTheme(theme);
        },

        setTheme(theme) {
            document.documentElement.setAttribute('data-theme', theme);
            localStorage.setItem(this.STORAGE_KEY, theme);
        },

        toggle() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === this.DARK ? this.LIGHT : this.DARK;
            this.setTheme(newTheme);
        },

        bindToggle() {
            const toggleBtn = document.getElementById('themeToggle');
            if (toggleBtn) {
                toggleBtn.addEventListener('click', () => this.toggle());
            }
        }
    };

    // ==========================================================================
    // Navbar Scroll Effect
    // ==========================================================================
    
    const NavbarScroll = {
        navbar: null,
        scrollThreshold: 50,

        init() {
            this.navbar = document.querySelector('.navbar');
            if (this.navbar) {
                this.handleScroll();
                window.addEventListener('scroll', () => this.handleScroll(), { passive: true });
            }
        },

        handleScroll() {
            if (window.scrollY > this.scrollThreshold) {
                this.navbar.classList.add('scrolled');
            } else {
                this.navbar.classList.remove('scrolled');
            }
        }
    };

    // ==========================================================================
    // Scroll Animations
    // ==========================================================================
    
    const ScrollAnimations = {
        observer: null,
        animatedElements: [],

        init() {
            this.animatedElements = document.querySelectorAll('.animate-on-scroll');
            
            if (this.animatedElements.length === 0) return;

            if ('IntersectionObserver' in window) {
                this.observer = new IntersectionObserver(
                    (entries) => this.handleIntersection(entries),
                    { threshold: 0.1, rootMargin: '0px 0px -50px 0px' }
                );

                this.animatedElements.forEach(el => this.observer.observe(el));
            } else {
                // Fallback for older browsers
                this.animatedElements.forEach(el => el.classList.add('visible'));
            }
        },

        handleIntersection(entries) {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    this.observer.unobserve(entry.target);
                }
            });
        }
    };

    // ==========================================================================
    // Smooth Scroll for Anchor Links
    // ==========================================================================
    
    const SmoothScroll = {
        init() {
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {
                anchor.addEventListener('click', (e) => this.handleClick(e, anchor));
            });
        },

        handleClick(e, anchor) {
            const href = anchor.getAttribute('href');
            if (href === '#') return;

            const target = document.querySelector(href);
            if (target) {
                e.preventDefault();
                const navbarHeight = document.querySelector('.navbar')?.offsetHeight || 0;
                const targetPosition = target.getBoundingClientRect().top + window.scrollY - navbarHeight - 20;

                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });

                // Close mobile menu if open
                const navbarCollapse = document.querySelector('.navbar-collapse');
                if (navbarCollapse?.classList.contains('show')) {
                    const bsCollapse = bootstrap.Collapse.getInstance(navbarCollapse);
                    if (bsCollapse) bsCollapse.hide();
                }
            }
        }
    };

    // ==========================================================================
    // Form Enhancements
    // ==========================================================================
    
    const FormEnhancements = {
        init() {
            this.initImagePreview();
            this.initFormValidation();
        },

        initImagePreview() {
            const imageUrlInput = document.getElementById('image_url');
            const imageFileInput = document.getElementById('image_file');
            const previewContainer = document.getElementById('imagePreview');
            const previewImg = document.getElementById('previewImg');

            if (imageUrlInput && previewContainer && previewImg) {
                imageUrlInput.addEventListener('input', function() {
                    if (this.value) {
                        previewImg.src = this.value;
                        previewContainer.classList.remove('d-none');
                    } else {
                        previewContainer.classList.add('d-none');
                    }
                });
            }

            if (imageFileInput && previewContainer && previewImg) {
                imageFileInput.addEventListener('change', function() {
                    const file = this.files[0];
                    if (file) {
                        const reader = new FileReader();
                        reader.onload = function(e) {
                            previewImg.src = e.target.result;
                            previewContainer.classList.remove('d-none');
                            if (imageUrlInput) imageUrlInput.value = '';
                        };
                        reader.readAsDataURL(file);
                    }
                });
            }
        },

        initFormValidation() {
            const forms = document.querySelectorAll('form[data-validate]');
            forms.forEach(form => {
                form.addEventListener('submit', function(e) {
                    if (!form.checkValidity()) {
                        e.preventDefault();
                        e.stopPropagation();
                    }
                    form.classList.add('was-validated');
                });
            });
        }
    };

    // ==========================================================================
    // Delete Confirmation
    // ==========================================================================
    
    const DeleteConfirmation = {
        init() {
            document.querySelectorAll('[data-confirm]').forEach(element => {
                element.addEventListener('click', function(e) {
                    const message = this.getAttribute('data-confirm') || 'Are you sure you want to delete this?';
                    if (!confirm(message)) {
                        e.preventDefault();
                    }
                });
            });
        }
    };

    // ==========================================================================
    // Auto-hide Alerts
    // ==========================================================================
    
    const AutoHideAlerts = {
        init() {
            const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
            alerts.forEach(alert => {
                setTimeout(() => {
                    const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                    bsAlert.close();
                }, 5000);
            });
        }
    };

    // ==========================================================================
    // Initialize Everything
    // ==========================================================================
    
    document.addEventListener('DOMContentLoaded', function() {
        ThemeManager.init();
        NavbarScroll.init();
        ScrollAnimations.init();
        SmoothScroll.init();
        FormEnhancements.init();
        DeleteConfirmation.init();
        AutoHideAlerts.init();
    });

})();
