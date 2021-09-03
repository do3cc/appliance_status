import $ from "jquery";

function extendButtonBehavior(button, form){
    button.attr("disabled", "true");
    form.change(function () {
        button.removeAttr("disabled");
    });
    return button;
}

function extendFormBehavior(form, form_error){
    form.submit(function (event) {
        var formData = {};
        event.preventDefault();
        form.find("input[type=text]").each(function (item) {
            formData[item.name] = item.value;
        });
        $.post("/update", form.serialize())
            .done(function (data) {
                form_error.hide();
                button.attr("disabled", "true");
            }).fail(function (data) {
                form_error.show();
            });
    });
    return form;
}

export {extendButtonBehavior, extendFormBehavior};