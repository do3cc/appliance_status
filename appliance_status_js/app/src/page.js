import {extendButtonBehavior, extendFormBehavior} from "./app";
import $ from "jquery";

$(document).ready(function () {
    var button = $("form#appliance_config input[type=submit]"),
        form = $("form#appliance_config"),
        form_error = $("#form_error");
    extendButtonBehavior(button, form);
    extendFormBehavior(form, form_error);
});

