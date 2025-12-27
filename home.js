// Fade-in animation on scroll
const faders = document.querySelectorAll('.fade-in');

const appearOnScroll = new IntersectionObserver(
  (entries, observer) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('show');
        observer.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.3 }
);

faders.forEach(fader => {
  appearOnScroll.observe(fader);
});
