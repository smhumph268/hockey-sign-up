$(document).ready(function() {
    var allSignUpButtons = document.querySelectorAll('a[id^=sign-up-toggle-]');
    // Add event listener to save changes
    for (var i = 0; i < allSignUpButtons.length; i++) {
        var dropIn = allSignUpButtons[i].id.replace("sign-up-toggle-", "");
        $("#message-"+dropIn).hide();
        if (usersDropInsJson.some(user_drop_in => user_drop_in.fields.dropIn == dropIn)) {
            $("#sign-up-as-goalie-div-"+dropIn).hide();
        }
        allSignUpButtons[i].addEventListener('click', function() {
            var dropIn = this.id.replace("sign-up-toggle-", "")
            var asGoalie = false
            if ($('#sign-up-as-goalie-'+dropIn).length > 0) {
                asGoalie = $('#sign-up-as-goalie-'+dropIn).is(":checked")
            }

            const targetDiv = document.getElementById("message-"+dropIn);
            const btn = document.getElementById("message-close-"+dropIn);
            btn.onclick = function () {
                if (targetDiv.style.display !== "none") {
                    targetDiv.style.display = "none";
                } else {
                    targetDiv.style.display = "block";
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
                        $("#sign-up-toggle-"+dropIn).text('Withdraw');
                        $("#sign-up-as-goalie-div-"+dropIn).hide();
                    }
                    else {
                        $("#sign-up-toggle-"+dropIn).text('Sign Up');
                        $("#sign-up-as-goalie-div-"+dropIn).show();
                    }
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