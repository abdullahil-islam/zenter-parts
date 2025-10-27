/** @odoo-module **/

import { Component, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class VendorFormAnimator extends Component {
    setup() {
        this._observer = null;
        onMounted(() => {
            const root = this.el?.closest(".o-vendor-form") || document;
            const elems = root.querySelectorAll("[data-animate]");
            if (!elems.length) {
                return;
            }
            // IntersectionObserver to add .in-view on scroll and initial load
            this._observer = new IntersectionObserver(
                (entries) => {
                    for (const e of entries) {
                        if (e.isIntersecting) {
                            e.target.classList.add("in-view");
                        }
                    }
                },
                { threshold: 0.15 }
            );
            elems.forEach((el) => this._observer.observe(el));

            // Ensure initial visible elements are animated (page load)
            requestAnimationFrame(() => {
                elems.forEach((el) => {
                    const rect = el.getBoundingClientRect();
                    if (rect.top >= 0 && rect.top < window.innerHeight) {
                        el.classList.add("in-view");
                    }
                });
            });
        });
        onWillUnmount(() => {
            if (this._observer) {
                this._observer.disconnect();
                this._observer = null;
            }
        });
    }
}
VendorFormAnimator.template = "bista_supplier_registration.FormAnimator";

// Auto-mount on the website via public_components
registry.category("public_components").add("vendor_form_animator", {
    component: VendorFormAnimator,
    selector: ".o-vendor-form",
});
