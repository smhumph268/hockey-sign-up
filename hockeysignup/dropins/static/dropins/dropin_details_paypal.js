function isJsonString(str) {
    try {
        JSON.parse(str);
    } catch (e) {
        return false;
    }
    return true;
}

// See: https://developer.paypal.com/sdk/js/reference/
paypal.Buttons({
    style: {
        shape: 'rect',
        color: 'gold',
        layout: 'horizontal',
        label: 'paypal',
    },

    onError(err) {
        var potentialErrorJsonObj = err.message.substring(err.message.indexOf('{'))
        if (isJsonString(potentialErrorJsonObj)) {
            $("#message-text").text('Failed to complete transaction. Reason: ' +
                JSON.parse(potentialErrorJsonObj).name +
                ' | Message: ' +
                JSON.parse(potentialErrorJsonObj).message
            );
        } else {
            $("#message-text").text('Failed to complete transaction. Message: ' + potentialErrorJsonObj);
        }
        $('.alert').addClass('alert-danger');
        $("#message").show();
    },

    // Create order
    createOrder: function(data, actions) {
        return actions.order.create({
            "application_context": {
                shipping_preference: "NO_SHIPPING",
            },
            purchase_units: [{
                amount: {
                    value: '5.00'
                },
                payee: {
                    email_address: "organizer-614-signup@personal.example.com",
                }
            }]
        });
    },

    // Finalize the transaction after payer approval
    onApprove: function(data, actions) {
        return actions.order.capture().then(function(details){
            $("#message-text").text('Transaction completed by ' + details.payer.name.given_name + '! You paid ' + details.purchase_units[0].amount.value + ' ' + details.purchase_units[0].amount.currency_code + ' using ' + data.paymentSource);
            $('.alert').addClass('alert-success');
            $("#message").show();
        });
    }
}).render('#paypal-button-container');