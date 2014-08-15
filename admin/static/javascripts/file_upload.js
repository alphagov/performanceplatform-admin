(function() {

  function createListElement(text) {
    var elem = document.createElement('li');
    elem.textContent = text;
    return elem;
  }

  function setMessage(className) {
    return function (file, message) {
      var form = $(file.previewElement).parent(),
          messageElem = form.find('.dz-message'),
          messageList = document.createElement('ul'),
          listItem;

      this.disable();

      if (message.payload) {
        if (message.payload.length) {
          for (var i = 0; i < message.payload.length; i++) {
            messageList.appendChild(
              createListElement(message.payload[i]));
          }
        } else {
            messageList.appendChild(
              createListElement(message.payload));
        }
      } else {
        messageList.appendChild(
            createListElement(message));
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
