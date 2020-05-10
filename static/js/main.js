var hamburger = document.getElementById("sidebar-nav");

$(window).resize(function () {
	let viewportWidth = $(window).width();
	if (viewportWidth > 768) {
		$("#sidebar-nav").removeClass('hide');
	} else {
		$("#sidebar-nav").addClass('hide');
	}
});

function toggle_sidebar() {
	hamburger.classList.toggle("hide");
}