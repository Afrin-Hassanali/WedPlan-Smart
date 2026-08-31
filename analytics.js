document.addEventListener("DOMContentLoaded", function () {

    /* =====================================================
       NAVIGATION MENU
    ===================================================== */

    const menuToggle = document.getElementById("menuToggle");
    const dashboardDropdown =
        document.getElementById("dashboardDropdown");

    if (menuToggle && dashboardDropdown) {

        menuToggle.addEventListener("click", function (event) {

            event.preventDefault();
            event.stopPropagation();

            const isOpen =
                dashboardDropdown.classList.toggle("show");

            menuToggle.setAttribute(
                "aria-expanded",
                isOpen ? "true" : "false"
            );

        });


        /* CLOSE WHEN CLICKING OUTSIDE */

        document.addEventListener("click", function (event) {

            if (
                !dashboardDropdown.contains(event.target) &&
                !menuToggle.contains(event.target)
            ) {

                dashboardDropdown.classList.remove("show");

                menuToggle.setAttribute(
                    "aria-expanded",
                    "false"
                );

            }

        });


        /* CLOSE AFTER CLICKING A MENU LINK */

        const menuLinks =
            dashboardDropdown.querySelectorAll("a");

        menuLinks.forEach(function (link) {

            link.addEventListener("click", function () {

                dashboardDropdown.classList.remove("show");

                menuToggle.setAttribute(
                    "aria-expanded",
                    "false"
                );

            });

        });

    }


    /* =====================================================
       BUDGET DONUT CHART
    ===================================================== */

    const donut =
        document.getElementById("budgetDonut");

    const legendItems =
        document.querySelectorAll(".legend-item");

    const colors = [
        "#D2A754",
        "#DE83AE",
        "#5B36A3",
        "#76A6C9",
        "#8DB58F"
    ];


    if (donut && legendItems.length > 0) {

        let currentAngle = 0;

        const gradients = [];


        legendItems.forEach(function (item, index) {

            let percentage =
                parseFloat(
                    item.getAttribute("data-percentage")
                );

            if (isNaN(percentage)) {
                percentage = 0;
            }


            const startAngle = currentAngle;

            const endAngle =
                currentAngle + (percentage * 3.6);


            gradients.push(
                colors[index % colors.length]
                + " "
                + startAngle
                + "deg "
                + endAngle
                + "deg"
            );


            currentAngle = endAngle;


            /* Legend dot */

            const dot =
                item.querySelector(".legend-dot");

            if (dot) {

                dot.style.backgroundColor =
                    colors[index % colors.length];

            }

        });


        /* Apply donut */

        if (gradients.length > 0) {

            donut.style.background =
                "conic-gradient("
                + gradients.join(", ")
                + ")";

        }

    }


    /* =====================================================
       EXPENSE PROGRESS BARS
    ===================================================== */

    const progressBars =
        document.querySelectorAll(
            ".expense-progress-fill"
        );


    progressBars.forEach(function (bar) {

        const percentage =
            parseFloat(
                bar.getAttribute("data-width")
            ) || 0;


        const index =
            parseInt(
                bar.getAttribute("data-index"),
                10
            ) || 0;


        bar.style.width =
            Math.min(
                Math.max(percentage, 0),
                100
            ) + "%";


        bar.style.backgroundColor =
            colors[index % colors.length];

    });

});