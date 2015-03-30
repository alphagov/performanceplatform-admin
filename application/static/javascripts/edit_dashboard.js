(function () {

  function setupJsonValidation($textareas) {
    $textareas.each(function() {
      $(this).on('keyup', function () {
        $(this).removeClass('invalid').next('.msg-invalid-json').remove();
        try {
          jsonlint.parse($(this).val());
        } catch (err) {
          $(this).addClass('invalid').after('<div class="msg-invalid-json">Invalid JSON: ' + err + '</div>');
          $(this).linedtextarea(
            {selectedLine: 1}
          );
        }
      });
    });
  }

  setupJsonValidation($('.json-field'));
  $('.js-sticky').stick_in_parent();

}());
