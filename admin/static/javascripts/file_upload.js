function setMessage(className) {
	return function (file, message) {
		var form = $(file.previewElement).parent(),
		    messageElem = form.find('.dz-message'),
		    messageList = document.createElement('ul');

		this.disable();

		for (var i = 0; i < message.payload.length; i++) {
			listItem = document.createElement('li');
			listItem.textContent = message.payload[i];
			messageList.appendChild(listItem);
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
