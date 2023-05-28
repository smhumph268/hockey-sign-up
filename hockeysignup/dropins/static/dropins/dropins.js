if (performance.navigation.type == performance.navigation.TYPE_RELOAD) {
    /* Upon re-loading, update session storage with values from server. This should help if the user refreshes the page
    after something is updated during another login session with their own account or an admin un-rosteres them, etc.

    see https://stackoverflow.com/questions/5004978/check-if-page-gets-reloaded-or-refreshed-in-javascript

    Based on the code in this file, all keys in the session storage are IDs of elements that appear on the pages that
    list dropins */
    for (var i = 0; i < sessionStorage.length; i++) {
        // Fine element with ID matching the key name from session storage
        var correspondingElement = document.querySelector('#'+sessionStorage.key(i))
        if(correspondingElement) {
            console.log("Found "+sessionStorage.key(i)+' value: '+sessionStorage.getItem(sessionStorage.key(i)));

            // text content of corresponding element reflects the new value from the server
            sessionStorage.setItem(sessionStorage.key(i), correspondingElement.textContent.trim());

            console.log("new value: "+sessionStorage.getItem(sessionStorage.key(i)));
        }
    }
}

function createPaymentButtonListenerIfExists(buttonIDText, paymentURL, dropIn) {
    // Add event listener for pay with paypal button - if it exists
    var paypalButton = document.querySelector('#'+buttonIDText+dropIn)
    if (paypalButton) {
        paypalButton.addEventListener('click', function() {
            var dropIn = this.id.replace(buttonIDText, "")

            // Make AJAX request to update model
            $.ajax({
                url: paymentURL,
                type: 'POST',
                data: {
                    'dropInToPayFor': dropIn,
                    csrfmiddlewaretoken: $("[name=csrfmiddlewaretoken]").val()
                },
                success: function(response) {
                    if (response.success) {
                        // Show the success message
                        $("#message-text-"+dropIn).text(response.text);
                        $("#message-div-"+dropIn).addClass('alert-success');
                        $("#message-"+dropIn).show();

                        // Hide payment buttons
                        $("#payment-buttons-"+dropIn).hide();

                        // Set 'You have paid.' text in session storage and display in the text element
                        sessionStorage.setItem('paid-text-'+dropIn, 'You have paid.');
                        $("#paid-text-"+dropIn).text(sessionStorage.getItem('paid-text-'+dropIn));
                        $("#paid-text-"+dropIn).css("color","green");
                    } else {
                        // Show the error message from response
                        $("#message-text-"+dropIn).text(response.text);
                        $("#message-div-"+dropIn).addClass('alert-danger');
                        $("#message-"+dropIn).show();
                    }
                },
                error: function(xhr, status, error) {
                    // Show the error message
                    $("#message-text-"+dropIn).text('Failed');
                    $("#message-div-"+dropIn).addClass('alert-danger');
                    $("#message-"+dropIn).show();
                }
            });
        });
    }
}

$(document).ready(function() {
    var allSignUpButtons = document.querySelectorAll('a[id^=sign-up-toggle-]');

    // Add event listener to save changes
    for (var i = 0; i < allSignUpButtons.length; i++) {
        var dropIn = allSignUpButtons[i].id.replace("sign-up-toggle-", "");

        // Hide the message div for the drop-in
        $("#message-"+dropIn).hide();

        // Get sign up text button text value from session storage if it's in there, otherwise original page value
        $("#sign-up-toggle-"+dropIn).text(sessionStorage.getItem('sign-up-toggle-'+dropIn) || allSignUpButtons[i].text.trim());
        if ($("#sign-up-toggle-"+dropIn).text() == 'Withdraw') {
            $("#sign-up-as-goalie-div-"+dropIn).hide();
        }

        // All drop-ins should have a rostered text. Color the 'rostered' text.
        $("#rostered-text-"+dropIn).text(sessionStorage.getItem('rostered-text-'+dropIn) || document.querySelector('#rostered-text-'+dropIn).textContent.trim());
        if ($("#rostered-text-"+dropIn).text().trim() == 'You are not rostered.') {
            $("#rostered-text-"+dropIn).css("color","red");
        } else {
            $("#rostered-text-"+dropIn).css("color","green");
        }

        // Color the 'paid' text if it's there
        var paidTextForDropIn = document.querySelector('#paid-text-'+dropIn)
        if (paidTextForDropIn) {
            // Get 'paid' text value from session storage if it's in there, otherwise original page value
            $("#paid-text-"+dropIn).text(sessionStorage.getItem('paid-text-'+dropIn) || paidTextForDropIn.textContent.trim());
            if ($("#paid-text-"+dropIn).text().trim() == 'You have not paid.') {
                // Make text red and show payment option buttons
                $("#paid-text-"+dropIn).css("color","red");
                $("#payment-buttons-"+dropIn).show();
            } else if ($("#paid-text-"+dropIn).text().trim() == 'You have paid.') {
                // Make text green and hide payment option buttons
                $("#paid-text-"+dropIn).css("color","green");
                $("#payment-buttons-"+dropIn).hide();
            } else {
                // User shouldn't see payment options or text
                $("#payment-buttons-"+dropIn).hide();
                $("#paid-text-"+dropIn).remove();
            }
        }

        // Create onclick function for the message box associated with the dropin
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

        // Add event listener for sign up buttons
        allSignUpButtons[i].addEventListener('click', function() {
            var dropIn = this.id.replace("sign-up-toggle-", "")
            var asGoalie = false
            if ($('#sign-up-as-goalie-'+dropIn).length > 0) {
                asGoalie = $('#sign-up-as-goalie-'+dropIn).is(":checked")
            }

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
                    // Show the success message
                    $("#message-text-"+dropIn).text(response.text);
                    $("#message-div-"+dropIn).addClass('alert-success');
                    $("#message-"+dropIn).show();

                    // Update display based on sign up vs withdraw action
                    if (response.text == 'Successfully signed up') {
                        sessionStorage.setItem('sign-up-toggle-'+dropIn, 'Withdraw')
                        $("#sign-up-as-goalie-div-"+dropIn).hide();
                        // remove paid-text for drop-in from session storage in case it exists - start fresh
                        sessionStorage.removeItem('paid-text-'+dropIn)
                        // similar for rostered-text - start fresh
                        sessionStorage.removeItem('rostered-text-'+dropIn)
                    }
                    else {
                        sessionStorage.setItem('sign-up-toggle-'+dropIn, 'Sign Up')
                        $("#sign-up-as-goalie-div-"+dropIn).show();
                        /* set paid-text for drop-in from session storage to N/A - if the session storage/paid element
                        is already there, we don't want the user to see it */
                        sessionStorage.setItem('paid-text-'+dropIn, 'N/A')
                        // Similar for rostered-text, but we want to show that user is no longer rostered
                        sessionStorage.setItem('rostered-text-'+dropIn, 'You are not rostered.');
                    }
                    // set the sign up text value from session storage
                    $("#sign-up-toggle-"+dropIn).text(sessionStorage.getItem('sign-up-toggle-'+dropIn));

                    /* If the request was successful, then the rostered text should be red no matter what and it
                    should say 'You are not rostered' because if you are just signing up, then you need an admin
                    to roster you and if you are withdrawing, then you are not rostered or signed up */
                    $("#rostered-text-"+dropIn).css("color","red");
                    $("#rostered-text-"+dropIn).text('You are not rostered.');

                    /* Similar for the paid text, always remove the paid-text element  b/c if the user is signing up,
                    then an admin will have to roster them before they should have payment option, and if the user is
                    withdrawing, then they shouldn't see this anymore */
                    $("#paid-text-"+dropIn).remove();
                    $("#payment-buttons-"+dropIn).hide();
                },
                error: function(xhr, status, error) {
                    // Show the error message
                    $("#message-text-"+dropIn).text('Failed to change sign up status');
                    $("#message-div-"+dropIn).addClass('alert-danger');
                    $("#message-"+dropIn).show();
                }
            });
        });

        // Add event listener for pay with paypal button
        createPaymentButtonListenerIfExists('pay-paypal-', payWithPayPalURL, dropIn);

        // Add event listener for pay with credits button
        createPaymentButtonListenerIfExists('pay-credits-', payWithCreditsURL, dropIn);
    }
});