import {extendButtonBehavior, extendFormBehavior} from "./app";

document.addEventListener("DOMContentLoaded", () => {
    const button = document.querySelector("form#appliance_config input[type='submit']");
    const form = document.querySelector("form#appliance_config");
    const form_error = document.querySelector("#form_error");
    extendButtonBehavior(button, form);
    extendFormBehavior(form, form_error);
});

