document.addEventListener('DOMContentLoaded', function () {
  var toggle = document.querySelector('.mobile-nav-toggle');
  var nav = document.querySelector('.main-nav');
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var isOpen = nav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    });

    nav.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', function () {
        nav.classList.remove('open');
        toggle.setAttribute('aria-expanded', 'false');
      });
    });
  }

  // Convert dashboard table headers to per-cell labels for small-screen card view.
  document.querySelectorAll('.dashboard-main .data-table').forEach(function (table) {
    var headers = Array.from(table.querySelectorAll('thead th')).map(function (th) {
      return th.textContent.trim();
    });

    if (!headers.length) {
      return;
    }

    table.querySelectorAll('tbody tr').forEach(function (row) {
      row.querySelectorAll('td').forEach(function (cell, index) {
        if (!cell.hasAttribute('data-label') && headers[index]) {
          cell.setAttribute('data-label', headers[index]);
        }
      });
    });
  });

  // Auto-dismiss flash messages after a few seconds
  document.querySelectorAll('.messages li').forEach(function (el) {
    setTimeout(function () {
      el.style.transition = 'opacity 0.4s ease';
      el.style.opacity = '0';
      setTimeout(function () { el.remove(); }, 400);
    }, 4000);
  });
});
