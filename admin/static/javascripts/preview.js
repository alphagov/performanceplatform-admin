var scrollToIdInIframe = function (id) {
  var src = $('iframe').attr('src');
  src = stripPreviousId(src);
  $('iframe').attr('src', src + "#" + id);
}

$('#navbar').on('activate.bs.scrollspy', function () {
  scrollToIdInIframe($('li.active a').attr('href').replace(/#/, ''));
})

var stripPreviousId = function (url) {
  return url.replace(/#[\w-]+$/, '');
};
