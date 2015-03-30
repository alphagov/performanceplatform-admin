(function () {

  function setQueryParamsFromModuleType() {
    $('.js-module-type-selector').on('change', function () {
      var type = $(this).find('[value="' + $(this).val() + '"]').text(),
        $queryParams = $('.js-query-parameters');

      $.getJSON('/static/json/' + type + '.json')
        .done(function (data) {
          $queryParams.val(JSON.stringify(data, null, '\t'));
        })
        .fail(function() {
          $queryParams.val('{}');
        });
    });
  }

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

  setQueryParamsFromModuleType();
  setupJsonValidation($('.json-field'));
  $('.js-sticky').stick_in_parent();

}());
