(function($) {
    $(document).ready(function() {
        var documentWidth = $(document).width();
        oldFunc = DateTimeShortcuts.openCalendar;
        DateTimeShortcuts.openCalendar = function(num) {
            oldFunc.call(DateTimeShortcuts, num);
            var calBox = $('#calendarbox'+num).get(0);
            var calBoxWidth = $(calBox).width();
            if(calBoxWidth + parseInt(calBox.style.left) > documentWidth) {
                calBox.style.left = documentWidth - calBoxWidth - 5 + 'px';
            }
            calBox.style.zIndex = 1001;
        }
    });
})(django.jQuery)


function focusOrOpen(link, name) {
    var popup = window.open('', name, 'height=500,width=800,resizable=yes,scrollbars=yes');
    if(popup.location.href != link.href) {
        popup.location.href = link.href;
    }
    popup.focus();
    return false;
}
