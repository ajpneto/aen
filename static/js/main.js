// ===== Navbar com efeito de scroll =====
const nav = document.getElementById('mainNav');
window.addEventListener('scroll', () => {
    if (window.scrollY > 50) {
        nav.style.padding = '0.4rem 0';
        nav.style.boxShadow = '0 4px 20px rgba(0,0,0,0.15)';
    } else {
        nav.style.padding = '0.8rem 0';
        nav.style.boxShadow = 'none';
    }
});

// ===== Fechar menu mobile ao clicar em link =====
document.querySelectorAll('#navMenu .nav-link').forEach(link => {
    link.addEventListener('click', () => {
        const collapse = document.getElementById('navMenu');
        if (collapse.classList.contains('show')) {
            new bootstrap.Collapse(collapse).hide();
        }
    });
});

// ===== Animação de fade-in ao rolar =====
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, { threshold: 0.12 });

document.querySelectorAll('.service-card, .step-card, .card').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(24px)';
    el.style.transition = 'opacity .6s ease, transform .6s ease';
    observer.observe(el);
});
