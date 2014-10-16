var scrollToIdInIframe = function (id) {
  var src = $('iframe').attr('src');
  src = stripPreviousId(src);
  $('iframe').attr('src', src + "#" + id);
}

$('#navbar').on('activate.bs.scrollspy', function () {
  var id = $('li.active a').attr('href').replace(/#/, '');
  scrollToIdInIframe(id);
  setFormPostQueryParam(id);
})

var stripPreviousId = function (url) {
  return url.replace(/#[\w-]+$/, '');
};

var stripPreviousPagePosition= function (url) {
  return url.replace(/\?[\w-=]+$/, '');
};

var setFormPostQueryParam = function (id) {
  var form = $('form');
  var previousUrl = form.attr('action');
  var previousUrl = stripPreviousPagePosition(previousUrl);
  form.attr('action', previousUrl+="?page_position="+id);
}
