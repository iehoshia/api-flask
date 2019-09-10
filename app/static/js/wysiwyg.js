$(document).ready(function() {
  $('#comment_content').on('input',function(e){
    console.log('Changed!',$('#comment_content').val())
  });
  $('#comment_content').summernote({
  toolbar: [
    // [groupName, [list of button]]
    ['style', ['bold', 'italic', 'underline', 'clear']],
    //['color', ['color']],
    ['para', ['ul', 'ol', 'paragraph']],
    //['height', ['height']],
    ['view', ['fullscreen', 'codeview', 'help']],
  ],
  codeviewFilter: false,
  codeviewIframeFilter: true,
  airMode: false,
});
  //$("#submit").click(function () {
  //      $("form").trigger("reset");
  //  });
});