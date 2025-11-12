// 粒子背景
particlesJS('particles-js', {
  particles: {
    number: { value: 80, density: { enable: true, value_area: 800 } },
    color: { value: '#00d4ff' },
    shape: { type: 'circle' },
    opacity: { value: 0.5, random: true },
    size: { value: 3, random: true },
    line_linked: { enable: true, distance: 150, color: '#00d4ff', opacity: 0.2, width: 1 },
    move: { enable: true, speed: 2 }
  },
  interactivity: { events: { onhover: { enable: true, mode: 'repulse' } } }
});

// 深色模式
document.getElementById('theme').addEventListener('change', e => {
  document.body.classList.toggle('dark', e.target.checked);
});

// 作品篩選
document.querySelectorAll('.filters button').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.filters button').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const filter = btn.getAttribute('data-filter');
    document.querySelectorAll('.card').forEach(card => {
      card.style.display = (filter === 'all' || card.getAttribute('data-category') === filter) ? 'block' : 'none';
    });
  });
});

// 搜尋
document.getElementById('search').addEventListener('input', function() {
  const query = this.value.toLowerCase();
  document.querySelectorAll('.card').forEach(card => {
    card.style.display = card.textContent.toLowerCase().includes(query) ? 'block' : 'none';
  });
});