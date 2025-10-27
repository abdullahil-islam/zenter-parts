/** @odoo-module */
import { AnalyticDistribution } from "@analytic/components/analytic_distribution/analytic_distribution";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

patch(AnalyticDistribution.prototype, {
    fetchPlansArgs(props) {
        const args = super.fetchPlansArgs(props);
        if (props.record.resModel) {
            args['current_model'] = props.record.resModel;
        }
        return args;
    }
})
