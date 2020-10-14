function animateValue(id, start, end, duration) {
    var obj = document.getElementById(id);
    var range = end - start;
    var current = start;
    var increment = 3;
    //var stepTime = Math.abs(Math.floor(duration / range));
    var stepTime = duration / range;
    var timer = setInterval(function() {
        current += increment;
        obj.innerHTML = '+'+current;
        if (current >= end) {
            clearInterval(timer);
        }
    }, stepTime);
}
document.addEventListener('DOMContentLoaded', function() {

    var value_element = document.getElementById('student-number');
    var value = value_element.innerHTML
    var element;
    var positionFromTop;

    function init() {
        element = document.getElementById('student-number');
        hideForm();
    }

    function checkPosition() {

        positionFromTop = element.getBoundingClientRect().top;

        if (positionFromTop < 950) {

            animateValue("student-number", 300, value, 100);
            window.removeEventListener('scroll', checkPosition);


        }

    }

    window.addEventListener('scroll', checkPosition);
    window.addEventListener('resize', init);

    init();
    checkPosition();

}, false);

/*
(function($) {


  $.fn.visible = function(partial) {

      var $t            = $(this),
          $w            = $(window),
          viewTop       = $w.scrollTop(),
          viewBottom    = viewTop + $w.height(),
          _top          = $t.offset().top,
          _bottom       = _top + $t.height(),
          compareTop    = partial === true ? _bottom : _top,
          compareBottom = partial === true ? _top : _bottom;

    return ((compareBottom <= viewBottom) && (compareTop >= viewTop));

  };

})(jQuery);

$(window).scroll(function(event) {

  $(".module").each(function(i, el) {
    var el = $(el);
    if (el.visible(true)) {
      el.addClass("come-in");
    }
  });

});
*/
$(window).scroll(function() {
    if ($(window).scrollTop() > 1800) {
        showForm();
        // > 100px from top - show div
    }
    else {
        hideForm();
    }
});

function showForm() {
  document.getElementById("myForm").style.display = "block";
}

function hideForm() {
  document.getElementById("myForm").style.display = "none";
}