document.addEventListener("DOMContentLoaded", function () {

    const menuToggle =
        document.getElementById("menuToggle");

    const dashboardMenu =
        document.getElementById("dashboardMenu");


    if (!menuToggle || !dashboardMenu) {
        return;
    }


    menuToggle.addEventListener("click", function (event) {

        event.stopPropagation();

        const isOpen =
            dashboardMenu.classList.toggle("show");

        menuToggle.setAttribute(
            "aria-expanded",
            isOpen ? "true" : "false"
        );

    });


    document.addEventListener("click", function (event) {

        if (
            !dashboardMenu.contains(event.target) &&
            !menuToggle.contains(event.target)
        ) {

            dashboardMenu.classList.remove("show");

            menuToggle.setAttribute(
                "aria-expanded",
                "false"
            );

        }

    });


    const menuLinks =
        dashboardMenu.querySelectorAll("a");


    menuLinks.forEach(function (link) {

        link.addEventListener("click", function () {

            dashboardMenu.classList.remove("show");

            menuToggle.setAttribute(
                "aria-expanded",
                "false"
            );

        });

    });

});