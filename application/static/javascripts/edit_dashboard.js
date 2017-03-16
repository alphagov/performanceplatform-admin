(function () {

  function filterDataTypeBySelectedGroup() {
    $('.data-group').each(function () {
      var data_group = $(this);
      var module_index = data_group.attr('id').replace('-data_group', '');
      var data_type = $('#' + module_index + '-data_type');
      data_group.on('change', function () {
        var group = data_group.val();
        data_type.children().show();
        data_type.children('[label!=' + group + ']').hide();
        data_type.val(data_type.find('[label=' + group  + '] option')[0].value);
      });
    });
  }

  function setQueryParamsFromModuleType() {
    $('.js-module-type-selector').on('change', function () {
      var type = $(this).find('[value="' + $(this).val() + '"]').text(),
        $queryParams = $(this).closest('.module').find('.js-query-parameters');
        $visualisationParams = $(this).closest('.module').find('.js-visualisation-parameters');

      $.getJSON('/static/json/' + type + '.json')
        .done(function (data) {
          $queryParams.val(JSON.stringify(data['query'], null, '\t'));
          $visualisationParams.val(JSON.stringify(data['visualisation'], null, '\t'));
        })
        .fail(function() {
          $queryParams.val('{}');
          $visualisationParams.val('{}');
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

  filterDataTypeBySelectedGroup();

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
