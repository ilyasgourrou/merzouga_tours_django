/* Admin : prévient quand les photos choisies dépassent la limite d'envoi de l'hébergeur (4,5 Mo sur Vercel).
   On garde une marge : 4 Mo en tout pour tous les fichiers du formulaire. */
(function () {
  'use strict';
  var LIMIT_BYTES = 4 * 1024 * 1024;

  function totalSize(form) {
    var total = 0;
    form.querySelectorAll('input[type="file"]').forEach(function (input) {
      Array.prototype.forEach.call(input.files || [], function (file) { total += file.size; });
    });
    return total;
  }

  document.addEventListener('change', function (event) {
    var input = event.target;
    if (!input || input.type !== 'file' || !input.form) { return; }
    var total = totalSize(input.form);
    if (total > LIMIT_BYTES) {
      var mb = (total / 1024 / 1024).toFixed(1).replace('.', ',');
      window.alert(
        'Les photos choisies pèsent ' + mb + ' Mo au total, ce qui dépasse la limite de 4 Mo par envoi de l\'hébergeur.\n\n' +
        'Réduisez-les (par exemple avec squoosh.app) ou enregistrez le circuit puis ajoutez les autres photos dans un second temps.'
      );
      input.value = '';
    }
  });
})();
