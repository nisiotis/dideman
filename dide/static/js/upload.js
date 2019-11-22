django.jQuery(document).ready(function() {

	django.jQuery('#photo-upload').on('submit', function(event) {

		event.preventDefault();
		var imagetypes = ['image/jpeg', 'image/png'];
		var formData = new FormData(django.jQuery('#photo-upload')[0]);
		var filetype = django.jQuery('#photo-upload')[0][2].files[0].type;
		var filesize = django.jQuery('#photo-upload')[0][2].files[0].size;
		if (imagetypes.indexOf(filetype) == -1 || filesize > 1048576) {
			alert ('Ο τύπος του αρχείου ή το μέγεθός του δεν υποστηρίζονται.');
		} else {
			django.jQuery.ajax({
				xhr : function() {
					var xhr = new window.XMLHttpRequest();

					xhr.upload.addEventListener('progress', function(e) {

						if (e.lengthComputable) {

							console.log('Bytes Loaded: ' + e.loaded);
							console.log('Total Size: ' + e.total);
							console.log('Percentage Uploaded: ' + (e.loaded / e.total))

							var percent = Math.round((e.loaded / e.total) * 100);

							django.jQuery('#progr').css('width', percent + '%');

						}

					});

					return xhr;
				},
				type : 'POST',
				url : django.jQuery('#link_id').val(),
				data : formData,
				processData : false,
				contentType : false,
				success : function() {
					window.location.href = django.jQuery('#link_id').val() + '?saved=true'
				}
			});
		}
	});

});