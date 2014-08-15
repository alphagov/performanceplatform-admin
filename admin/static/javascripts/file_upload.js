(function() {

  function setMessage(className) {
    return function (file, message) {
      var form = $(file.previewElement).parent(),
          messageElem = form.find('.dz-message'),
          messageList = document.createElement('ul'),
          listItem;

      this.disable();

      messageList.className = 'list-unstyled';

      function addToList(text) {
        var elem = document.createElement('li');
        elem.textContent = text;
        messageList.appendChild(elem);
      }

      if (message.payload) {
        if (message.payload.length) {
          addToList('Failed to upload to ' + message.data_type + ':');
          for (var i = 0; i < message.payload.length; i++) {
            addToList(message.payload[i]);
          }
        } else {
            addToList('Your data uploaded successfully to ' + message.data_type +
                '. In about 20 minutes your data will appear on the relevant dashboards.');
        }
      } else {
        addToList(message);
      }

      messageElem.empty().append(messageList);
      form.addClass(className);
    }
  }


  window.Dropzone.prototype.defaultOptions['maxFiles'] = 1;
  window.Dropzone.prototype.defaultOptions['previewTemplate'] = '<div></div>';
  window.Dropzone.prototype.defaultOptions['init'] = function() {
    this.on("error", setMessage('error'));
    this.on("success", setMessage('success'));
    this.on("sending", function(file) {
      $(file.previewElement)
        .parent()
        .find('.dz-message')
        .text('Uploading ' + file.name + '...');
    });
  }

})();
