import {patch} from "@web/core/utils/patch";
import {registry} from "@web/core/registry";

export function addAltchaSteps(trigger) {
    return {
        steps() {
            const steps = super.steps();
            const nameStep = steps.findIndex((x) => x.trigger === trigger);
            if (nameStep >= 0) {
                steps.splice(
                    nameStep,
                    0,
                    {
                        content: "Verify altcha",
                        trigger: "altcha-widget input[type='checkbox']",
                        run: "click",
                    },
                    {
                        content: "Verify altcha value exists",
                        trigger: "input[name='altcha']:not(:visible):not(:empty)",
                    }
                );
            }
            return steps;
        },
    };
}

patch(
    registry.category("web_tour.tours").get("crowdfunding_frontend_us"),
    addAltchaSteps("input#name")
);
patch(
    registry.category("web_tour.tours").get("crowdfunding_frontend_nl"),
    addAltchaSteps("input#name")
);
