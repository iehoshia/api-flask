/*
var socket = io.connect('https://' + document.domain + ':' + location.port);//+'/'+location.pathname);
socket.on( 'connect', function() {
  socket.emit( 'my event', {
    data: 'User Connected'
  } )
  var form = $( 'form' ).on( 'submit', function( e ) {
    e.preventDefault()
    let user_name = $( 'input.username' ).val()
    let user_input = $( 'input.message' ).val()
    socket.emit( 'my event', {
      user_name : user_name,
      message : user_input
    } )
    $( 'input.message' ).val( '' ).focus()
  } )
} )
socket.on( 'my response', function( msg ) {
  console.log( msg )
  if( typeof msg.user_name !== 'undefined' ) {
    $( 'h3' ).remove()
    $( 'div.message_holder' ).append( '<div><b style="color: #000">'+msg.user_name+'</b> '+msg.message+'</div>' )
  }
})

var socket;
$(document).ready(function(){
    socket = io.connect('http://' + document.domain + ':' + location.port + '/' + location.pathname);
    socket.on('connect', function() {
        socket.emit('joined', {});
    });
    socket.on('status', function(data) {
        $('#chat').val($('#chat').val() + '<' + data.msg + '>\n');
        $('#chat').scrollTop($('#chat')[0].scrollHeight);
    });
    socket.on('message', function(data) {
        $('#chat').val($('#chat').val() + data.msg + '\n');
        $('#chat').scrollTop($('#chat')[0].scrollHeight);
    });
    $('#text').keypress(function(e) {
        var code = e.keyCode || e.which;
        if (code == 13) {
            text = $('#text').val();
            $('#text').val('');
            socket.emit('text', {msg: text});
        }
    });
});
function leave_room() {
    socket.emit('left', {}, function() {
        socket.disconnect();
        // go back to the login page
        window.location.href = "{{ url_for('main.index') }}";
    });
}
var socket;
$(document).ready(function(){
    console.log(location.pathname)
    socket = io.connect('https://' + document.domain + ':' + location.port);//+'/'+location.pathname);

    socket.on( 'connect', function() {
      socket.emit( 'my event', {
        data: 'User Connected'
      } )
      var form = $( 'form' ).on( 'submit', function( e ) {
        e.preventDefault()
        let user_name = $( 'input.username' ).val()
        let user_input = $( 'input.message' ).val()
        socket.emit( 'my event', {
          user_name : user_name,
          message : user_input
        } )
        $( 'input.message' ).val( '' ).focus()
      } )
    } )
    socket.on( 'my response', function( msg ) {
      console.log( msg )
      if( typeof msg.user_name !== 'undefined' ) {
        $( 'h3' ).remove()
        $( 'div.message_holder' ).append( '<div><b style="color: #000">'+msg.user_name+'</b> '+msg.message+'</div>' )
      }
    })
});

*/