(function () {

  function setQueryParamsFromModuleType() {
    $('.js-module-type-selector').on('change', function () {
      var type = $(this).find('[value="' + $(this).val() + '"]').text(),
        $queryParams = $(this).closest('.module').find('.js-query-parameters');

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

  function getModuleOrder() {
    var modules = [];
    $('.modules-list li').each(function() {
      modules.push($(this).attr('data-index'));
    });
    return modules.join(',');
  }

  setQueryParamsFromModuleType();

  setupJsonValidation($('.json-field'));

  $('.js-sticky').stick_in_parent();
  Sortable.create($('.modules-list')[0], {
    ghostClass: 'sortable-ghost',
    onUpdate: function() {
      if (!$('.modules-order').length) {
        $('.frm-dashboard').prepend('<input name="modules_order" class="modules-order" type="hidden" value="" />');
      }
    }
  });
  $('.frm-dashboard').on('submit', function() {
    $(this).find('input[type="hidden"].modules-order').val(getModuleOrder());
  });

}());
