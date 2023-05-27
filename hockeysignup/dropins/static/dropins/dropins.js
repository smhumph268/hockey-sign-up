$(document).ready(function() {
    var allSignUpButtons = document.querySelectorAll('a[id^=sign-up-toggle-]');

    // Add event listener to save changes
    for (var i = 0; i < allSignUpButtons.length; i++) {
        var dropIn = allSignUpButtons[i].id.replace("sign-up-toggle-", "");
        $("#message-"+dropIn).hide();
        // Get sign up text button text value from session storage if it's in there, otherwise original page value
        $("#sign-up-toggle-"+dropIn).text(sessionStorage.getItem('sign-up-toggle-'+dropIn) || allSignUpButtons[i].text.trim());
        if ($("#sign-up-toggle-"+dropIn).text() == 'Withdraw') {
            $("#sign-up-as-goalie-div-"+dropIn).hide();
        }
        allSignUpButtons[i].addEventListener('click', function() {
            var dropIn = this.id.replace("sign-up-toggle-", "")
            var asGoalie = false
            if ($('#sign-up-as-goalie-'+dropIn).length > 0) {
                asGoalie = $('#sign-up-as-goalie-'+dropIn).is(":checked")
            }

            const dropInMessageDiv = document.getElementById("message-"+dropIn);
            const btn = document.getElementById("message-close-"+dropIn);
            btn.onclick = function () {
                if (dropInMessageDiv.style.display !== "none") {
                    dropInMessageDiv.style.display = "none";
                } else {
                    dropInMessageDiv.style.display = "block";
                }
                if ($('#message-div-'+dropIn).hasClass('alert-danger')) {
                    $('#message-div-'+dropIn).removeClass('alert-danger');
                }
                if ($('#message-div-'+dropIn).hasClass('alert-success')) {
                    $('#message-div-'+dropIn).removeClass('alert-success');
                }
            };

            // Make AJAX request to update model
            $.ajax({
                url: toggleSignUpURL,
                type: 'POST',
                data: {
                    'dropInToToggle': dropIn,
                    'asGoalie': asGoalie,
                    csrfmiddlewaretoken: $("[name=csrfmiddlewaretoken]").val()
                },
                success: function(response) {
                    $("#message-text-"+dropIn).text(response.text);
                    $("#message-div-"+dropIn).addClass('alert-success');
                    $("#message-"+dropIn).show();
                    if (response.text == 'Successfully signed up') {
                        sessionStorage.setItem('sign-up-toggle-'+dropIn, 'Withdraw')
                        $("#sign-up-as-goalie-div-"+dropIn).hide();
                    }
                    else {
                        sessionStorage.setItem('sign-up-toggle-'+dropIn, 'Sign Up')
                        $("#sign-up-as-goalie-div-"+dropIn).show();
                    }
                    $("#sign-up-toggle-"+dropIn).text(sessionStorage.getItem('sign-up-toggle-'+dropIn));
                },
                error: function(xhr, status, error) {
                    $("#message-text-"+dropIn).text('Failed to change sign up status');
                    $("#message-div-"+dropIn).addClass('alert-danger');
                    $("#message-"+dropIn).show();
                }
            });
        });
    }
});