$(document).ready(function () {
    var button = $("form#appliance_config input[type=submit]"),
        form = $("form#appliance_config"),
        form_error = $("#form_error");
    button.hide()
    button.attr("disabled", "true");
    form.change(function () {
        button.removeAttr("disabled");
    });
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
            })
            ;
    })
})
