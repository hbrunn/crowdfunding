odoo.define("crowdfunding.tours.crowdfunding_frontend", function (require) {
    "use strict";

    const tour = require("web_tour.tour");

    tour.register(
        "crowdfunding_frontend",
        {
            test: true,
            url: "/crowdfunding",
        },
        [
            {
                content: "Select the first challenge",
                trigger: "main .card a[href$='-1']",
            },
            {
                content: "Click the pledge button",
                trigger: "main .nav a[href$='crowdfunding/1/pay']",
            },
            {
                content: "Fill in your name",
                trigger: "input#name",
                run: "text Firstname Lastname",
            },
            {
                content: "Fill in your email",
                trigger: "input#email",
                run: "text firstname.lastname@email.com",
            },
            {
                content: "Fill in your street",
                trigger: "input#street",
                run: "text Streetname 42",
            },
            {
                content: "Fill in your city",
                trigger: "input#city",
                run: "text Testcity",
            },
            {
                content: "Fill in your country",
                trigger: "select#country_id",
                run: () => {
                    $("select#country_id option:nth-child(2)").prop("selected", true);
                },
            },
            {
                content: "Submit your credentials",
                trigger: "main form button[type='submit']",
            },
            {
                content: "Fill in an amount",
                trigger: "main input#amount",
                run: "text 4242",
            },
            {
                content: "Submit amount",
                trigger: "main form button[type='submit']",
            },
            {
                content: "Submit payment",
                trigger: "main form button#o_payment_form_pay",
            },
            {
                content: "Last trigger",
                trigger: "body",
            },
        ]
    );
});
