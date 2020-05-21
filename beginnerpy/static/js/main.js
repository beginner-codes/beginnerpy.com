var sidebar = document.getElementById("sidebar-nav");

$(window).resize(function () {
	let viewportWidth = $(window).width();
	if (viewportWidth > 768) {
		$("#sidebar-nav").css("display", "");
	} else {
		$("#sidebar-nav").css("display", "none");
	}
});

function toggle_sidebar() {
	sidebar.classList.toggle("mobile-hidden");
}