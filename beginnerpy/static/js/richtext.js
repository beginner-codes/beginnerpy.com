DecoupledDocumentEditor.create( document.querySelector( '#summary_field' ), {
	toolbar: {
		items: [
			'heading',
			'|',
			'fontSize',
			'fontFamily',
			'fontColor',
			'|',
			'bold',
			'italic',
			'underline',
			'strikethrough',
			'|',
			'code',
			'codeBlock',
			'|',
			'numberedList',
			'bulletedList',
			'|',
			'indent',
			'outdent',
			'|',
			'alignment',
			'|',
			'link',
			'blockQuote',
			'|',
			'insertTable',
			'imageUpload',
			'mediaEmbed',
			'|',
			'CKFinder'
		]
	},
	language: 'en',
	image: {
		toolbar: [
			'imageTextAlternative',
			'imageStyle:full',
			'imageStyle:side'
		]
	},
	table: {
		contentToolbar: [
			'tableColumn',
			'tableRow',
			'mergeTableCells'
		]
	},
	licenseKey: '',
	
} )
.then( editor => {
	window.editor = editor;

	// Set a custom container for the toolbar.
	document.querySelector( '#toolbar1' ).appendChild( editor.ui.view.toolbar.element );
	document.querySelector( '.ck-toolbar' ).classList.add( 'ck-reset_all' );
} )
.catch( error => {
	console.error( 'Oops, something gone wrong!' );
	console.error( 'Please, report the following error in the https://github.com/ckeditor/ckeditor5 with the build id and the error stack trace:' );
	console.warn( 'Build id: f7ikzu9k2y2g-83370ydhbsar' );
	console.error( error );
} );


DecoupledDocumentEditor.create( document.querySelector( '#content_field' ), {
	toolbar: {
		items: [
			'heading',
			'|',
			'fontSize',
			'fontFamily',
			'fontColor',
			'|',
			'bold',
			'italic',
			'underline',
			'strikethrough',
			'|',
			'code',
			'codeBlock',
			'|',
			'numberedList',
			'bulletedList',
			'|',
			'indent',
			'outdent',
			'|',
			'alignment',
			'|',
			'link',
			'blockQuote',
			'|',
			'insertTable',
			'imageUpload',
			'mediaEmbed',
			'|',
			'CKFinder'
		]
	},
	language: 'en',
	image: {
		toolbar: [
			'imageTextAlternative',
			'imageStyle:full',
			'imageStyle:side'
		]
	},
	table: {
		contentToolbar: [
			'tableColumn',
			'tableRow',
			'mergeTableCells'
		]
	},
	licenseKey: '',
	
} )
.then( editor => {
	window.editor = editor;

	// Set a custom container for the toolbar.
	document.querySelector( '#toolbar2' ).appendChild( editor.ui.view.toolbar.element );
	document.querySelector( '.ck-toolbar' ).classList.add( 'ck-reset_all' );
} )
.catch( error => {
	console.error( 'Oops, something gone wrong!' );
	console.error( 'Please, report the following error in the https://github.com/ckeditor/ckeditor5 with the build id and the error stack trace:' );
	console.warn( 'Build id: f7ikzu9k2y2g-83370ydhbsar' );
	console.error( error );
} );




function trackEditor(element) {
	if (element.getAttribute("name") == "summary_field") {
		$("#toolbar1").removeClass("hide");
		$("#toolbar2").addClass("hide");
	} else if (element.getAttribute("name") == "content_field") {
		$("#toolbar1").addClass("hide");
		$("#toolbar2").removeClass("hide");
	}
}



function submitForm() {
	$("#summary").val($("#summary_field").html());
	$("#content").val($("#content_field").html());
	$("#article_form").submit();
}