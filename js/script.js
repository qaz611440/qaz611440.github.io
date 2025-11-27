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

// --- 篩選與搜尋功能 ---
let currentFilter = 'all';
const filters = document.querySelectorAll('.filters button');
const searchInput = document.getElementById('search');
const cards = document.querySelectorAll('.card');

filters.forEach(btn => {
  btn.addEventListener('click', () => {
    filters.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentFilter = btn.dataset.filter;
    filterProjects();
  });
});

searchInput.addEventListener('input', () => {
  filterProjects();
});

function filterProjects() {
  const query = searchInput.value.toLowerCase();
  cards.forEach(card => {
    const category = card.dataset.category;
    const text = card.textContent.toLowerCase();
    const matchCategory = (currentFilter === 'all' || category === currentFilter);
    const matchSearch = text.includes(query);

    if (matchCategory && matchSearch) {
      card.classList.remove('hidden');
    } else {
      card.classList.add('hidden');
    }
  });
}

// --- 燈箱控制 ---
const lightbox = document.getElementById('imageLightbox');
const lightboxImg = document.getElementById('lightboxImg');

function openImage(src) {
  lightbox.style.display = "block";
  lightboxImg.src = src;
}

function closeLightbox() {
  lightbox.style.display = "none";
}

window.onclick = function(event) {
  if (event.target == lightbox) {
    lightbox.style.display = "none";
  }
}

// --- 回到頂部按鈕 ---
const backToTopBtn = document.getElementById("backToTop");

window.onscroll = function() {
  // 顯示/隱藏回到頂部按鈕
  if (document.body.scrollTop > 300 || document.documentElement.scrollTop > 300) {
    backToTopBtn.classList.add("show");
  } else {
    backToTopBtn.classList.remove("show");
  }
  
  // 導覽列 Active 狀態切換
  highlightNav();
};

backToTopBtn.addEventListener("click", function() {
  window.scrollTo({ top: 0, behavior: 'smooth' });
});

// --- 導覽列滾動監聽 ---
const sections = document.querySelectorAll("section");
const navLinks = document.querySelectorAll(".nav-link");

function highlightNav() {
  let scrollY = window.scrollY;
  
  sections.forEach(current => {
    const sectionHeight = current.offsetHeight;
    const sectionTop = current.offsetTop - 100; // 減去 Navbar 高度誤差
    const sectionId = current.getAttribute("id");
    
    if (scrollY > sectionTop && scrollY <= sectionTop + sectionHeight) {
      navLinks.forEach(link => {
        link.classList.remove("active");
        if (link.getAttribute("href").includes(sectionId)) {
          link.classList.add("active");
        }
      });
    }
  });
}

// --- 初始化 ---
document.addEventListener('DOMContentLoaded', () => {
  document.querySelector('.filters button[data-filter="all"]').classList.add('active');
  filterProjects();
});

// ... (保留原本的代碼) ...

// ==================== 打字機特效邏輯 ====================
const textsToType = [
  "類比IC設計工程師",
  "Power 測試工程師",
  "AI 自動化工程師",
  "熱愛挑戰與解決問題"
];
const typeWriterElement = document.querySelector('.typewriter-text');
let textIndex = 0;
let charIndex = 0;
let isDeleting = false;
let typeSpeed = 100;

function typeWriter() {
  const currentText = textsToType[textIndex];
  
  if (isDeleting) {
    // 刪除文字中
    typeWriterElement.textContent = currentText.substring(0, charIndex - 1);
    charIndex--;
    typeSpeed = 50; // 刪除速度較快
  } else {
    // 輸入文字中
    typeWriterElement.textContent = currentText.substring(0, charIndex + 1);
    charIndex++;
    typeSpeed = 100; // 輸入速度正常
  }

  if (!isDeleting && charIndex === currentText.length) {
    // 打完一句，暫停一下
    isDeleting = true;
    typeSpeed = 2000; 
  } else if (isDeleting && charIndex === 0) {
    // 刪完一句，切換下一句
    isDeleting = false;
    textIndex = (textIndex + 1) % textsToType.length;
    typeSpeed = 500;
  }

  setTimeout(typeWriter, typeSpeed);
}

// 啟動打字機
document.addEventListener('DOMContentLoaded', () => {
  // 原本的初始化
  document.querySelector('.filters button[data-filter="all"]').classList.add('active');
  filterProjects();
  
  // 啟動打字機
  if(document.querySelector('.typewriter-text')) {
    typeWriter();
  }
});