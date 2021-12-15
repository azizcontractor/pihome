function reboot() {
    let confirmed = confirm('Are you sure you want to reboot the system? Data loss may occur.');
    if (confirmed) {
        $("div#reboot_modal").show();
        $.ajax({
            url: "/system/reboot",
            method: "GET",
            data: {},
            global: false,
            success: function (response) {
                console.log(response);
            },
        });
    }
}

function show_slides() {
    window.location.href = '/show/slides';
}