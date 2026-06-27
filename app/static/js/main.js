// Auto-dismiss notification alerts after 5 seconds
document.addEventListener('DOMContentLoaded', () => {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            setTimeout(() => {
                alert.remove();
            }, 400);
        }, 5000);
    });

    // Theme Toggle Switch handler
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    if (themeToggleBtn) {
        const themeIcon = themeToggleBtn.querySelector('i');
        
        // Setup initial icon state based on active class
        if (document.body.classList.contains('light-theme')) {
            themeIcon.className = 'fa-solid fa-sun';
        } else {
            themeIcon.className = 'fa-solid fa-moon';
        }
        
        themeToggleBtn.addEventListener('click', () => {
            document.body.classList.toggle('light-theme');
            let theme = 'dark';
            if (document.body.classList.contains('light-theme')) {
                theme = 'light';
                themeIcon.className = 'fa-solid fa-sun';
            } else {
                themeIcon.className = 'fa-solid fa-moon';
            }
            localStorage.setItem('theme', theme);
        });
    }
});

