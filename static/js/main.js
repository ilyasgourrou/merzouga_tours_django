(function () {
  'use strict';

  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- Menu mobile / tablette ---------- */
  var toggle = document.querySelector('.nav-toggle');
  var nav = document.getElementById('site-nav');

  if (toggle && nav) {
    var icon = toggle.querySelector('i');

    var setOpen = function (open) {
      nav.classList.toggle('is-open', open);
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      toggle.setAttribute('aria-label', open ? toggle.dataset.labelClose : toggle.dataset.labelOpen);
      if (icon) {
        icon.classList.toggle('fa-bars', !open);
        icon.classList.toggle('fa-xmark', open);
      }
    };

    toggle.addEventListener('click', function () {
      setOpen(!nav.classList.contains('is-open'));
    });

    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && nav.classList.contains('is-open')) {
        setOpen(false);
        toggle.focus();
      }
    });

    document.addEventListener('click', function (event) {
      if (nav.classList.contains('is-open') && !nav.contains(event.target) && !toggle.contains(event.target)) {
        setOpen(false);
      }
    });

    var desktop = window.matchMedia('(min-width: 1024px)');
    var onBreakpoint = function (event) { if (event.matches) { setOpen(false); } };
    if (desktop.addEventListener) { desktop.addEventListener('change', onBreakpoint); }
    else if (desktop.addListener) { desktop.addListener(onBreakpoint); }
  }

  /* ---------- Sélecteur de langue ----------
     Fonctionne sans JavaScript (formulaire POST vers set_language).
     Ici, on laisse juste la transition de couleur se voir avant l'envoi. */
  document.querySelectorAll('[data-lang-switch]').forEach(function (form) {
    var sending = false;

    form.addEventListener('submit', function (event) {
      var button = event.submitter;
      if (sending || !button) { return; }               // 2e passage ou navigateur sans submitter : envoi normal

      if (button.classList.contains('is-active')) {      // déjà la langue courante
        event.preventDefault();
        return;
      }
      if (reduceMotion) { return; }

      event.preventDefault();
      sending = true;
      form.querySelectorAll('.lang-switch__btn').forEach(function (b) {
        b.classList.toggle('is-active', b === button);
      });
      window.setTimeout(function () { form.requestSubmit(button); }, 180);
    });
  });

  /* ---------- Copier le code de réservation ---------- */
  document.querySelectorAll('[data-copy-target]').forEach(function (button) {
    var label = button.querySelector('span');
    button.addEventListener('click', function () {
      var source = document.getElementById(button.dataset.copyTarget);
      if (!source) { return; }
      var text = source.textContent.trim();
      var done = function () {
        if (label) { label.textContent = button.dataset.labelDone; }
        window.setTimeout(function () { if (label) { label.textContent = button.dataset.labelCopy; } }, 2000);
      };
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(done);
      } else {                                      // navigateurs anciens / http local
        var range = document.createRange();
        range.selectNodeContents(source);
        var selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);
        try { document.execCommand('copy'); done(); } catch (e) { /* le code reste sélectionné */ }
      }
    });
  });
})();
