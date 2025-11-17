/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";

    publicWidget.registry.SignupChoice = publicWidget.Widget.extend({
    selector: ".oe_website_login_container",
    disabledInEditableMode: false,
//    events: {
//        "click #ssf_btn_customer": "_onSelectCustomer",
//    },
    start: async function () {
        await this._super(...arguments);

        const params = new URLSearchParams(window.location.search);
        if (params.has("token")) {
            // Skip showing the modal if token is present
            return;
        }
        
        const el = document.getElementById("ssfSignupChoiceModal");
        if (!el) return;

        // Force static backdrop to block the signup form until selection
        if (window.bootstrap?.Modal) {
            const modal = new window.bootstrap.Modal(el, { backdrop: "static", keyboard: false });
            modal.show();
            this._modal = modal;
        } else {
            // Fallback if bootstrap not found
            el.classList.add("show");
            el.style.display = "block";
        }
    }
})
