var scrollToIdInIframe = function (id) {
  var src = $('iframe').attr('src');
  $('iframe').attr('src', src + "#" + id);
}

$('#myScrollspy').on('activate.bs.scrollspy', function () {
  alert('123');
  // do something…
})
