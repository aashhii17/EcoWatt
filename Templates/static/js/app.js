/**
 * VoltPulse Enterprise - Global JavaScript Application Controller
 */

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initSidebarToggle();
  initTableSearch();
});

// Theme Switcher & Persistence
function initTheme() {
  const savedTheme = localStorage.getItem('voltpulse_theme') || 'dark';
  if (savedTheme === 'light') {
    document.body.classList.add('light-theme');
  }
}

function toggleTheme() {
  document.body.classList.toggle('light-theme');
  const isLight = document.body.classList.contains('light-theme');
  localStorage.setItem('voltpulse_theme', isLight ? 'light' : 'dark');
}

// Sidebar Toggle (Mobile / Compact Viewports)
function initSidebarToggle() {
  const toggleBtn = document.getElementById('sidebarToggleBtn');
  const sidebar = document.getElementById('appSidebar');

  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', () => {
      sidebar.classList.toggle('active');
    });
  }
}

// Interactive Table Search Filter
function initTableSearch() {
  const searchInput = document.getElementById('tableSearchInput');
  const table = document.querySelector('table.enterprise-table');

  if (searchInput && table) {
    searchInput.addEventListener('input', (e) => {
      const query = e.target.value.toLowerCase().trim();
      const rows = table.querySelectorAll('tbody tr');

      rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        if (text.includes(query)) {
          row.style.display = '';
        } else {
          row.style.display = 'none';
        }
      });
    });
  }
}

// Modal Control Helpers
function openModal(modalId = 'addModal') {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('active');
  }
}

function closeModal(modalId = 'addModal') {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('active');
  }
}

// Close Modal on Overlay Click
document.addEventListener('click', (e) => {
  if (e.target.classList.contains('modal-overlay')) {
    e.target.classList.remove('active');
  }
});
