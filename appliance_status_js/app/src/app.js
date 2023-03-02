function extendButtonBehavior(button, form){
    button.setAttribute("disabled", "disabled");
    form.addEventListener("change", () => {
        button.removeAttribute("disabled");
    });
    return button;
}

function extendFormBehavior(form, form_error){
    form.addEventListener("submit", (event) => {
        const button = form.querySelector("input[type='submit']");
        const req = new XMLHttpRequest();

        event.preventDefault();

        req.onreadystatechange = () => {
            if (req.readyState === XMLHttpRequest.DONE) {
                if (req.status < 300) {
                    form_error.style.display = 'none';
                    button.setAttribute("disabled", "true");
                } else {
                form_error.style.display = '';
                }
            }
        }

        req.open("POST", "/update");
        req.send(new FormData(form));
    });
    return form;
}

export {extendButtonBehavior, extendFormBehavior};
