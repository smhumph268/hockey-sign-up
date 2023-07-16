sortable('#unassigned-sign-ups', {
    acceptFrom: '#white-team,#dark-team,#unassigned-sign-ups',
    placeholderClass: 'list-group-item col-md-6 sortable-placeholder-border'
});
sortable('#white-team', {
    acceptFrom: '#white-team,#dark-team,#unassigned-sign-ups',
    placeholderClass: 'list-group-item col-md-6 sortable-placeholder-border'
});
sortable('#dark-team', {
    acceptFrom: '#white-team,#dark-team,#unassigned-sign-ups',
    placeholderClass: 'list-group-item col-md-6 sortable-placeholder-border'
});

$(document).ready(function() {
    $("#message").hide();
    // Add event listener to save changes
    $('#save-button').click(function(){
        // Extract player IDs from updated team rosters
        var whiteTeam = $('#white-team').find('.list-group-item').map(function() {
            return $(this).data('id');
        }).get();

        var darkTeam = $('#dark-team').find('.list-group-item').map(function() {
            return $(this).data('id');
        }).get();

        var unassignedPlayers = $('#unassigned-sign-ups').find('.list-group-item').map(function() {
            return $(this).data('id');
        }).get();

        // Make AJAX request to update model
        $.ajax({
            url: updateRostersURL,
            type: 'POST',
            data: {
                'white_team_sign_up_ids': whiteTeam,
                'dark_team_sign_up_ids': darkTeam,
                'unassigned_ids': unassignedPlayers,
                csrfmiddlewaretoken: $("[name=csrfmiddlewaretoken]").val()
            },
            success: function(response) {
                $("#message-text").text('Successfully saved rosters. If you navigate away from this page, you may need to reload when you return to see the changes.');
                $('.alert').addClass('alert-success');
                $("#message").show();
            },
            error: function(xhr, status, error) {
                $("#message-text").text('Failed to save rosters');
                $('.alert').addClass('alert-danger');
                $("#message").show();
            }
        });
    });
});

const targetDiv = document.getElementById("message");
const btn = document.getElementById("messageClose");
btn.onclick = function () {
    if (targetDiv.style.display !== "none") {
        targetDiv.style.display = "none";
    } else {
        targetDiv.style.display = "block";
    }
    if ($('.alert').hasClass('alert-danger')) {
        $('.alert').removeClass('alert-danger');
    }
    if ($('.alert').hasClass('alert-success')) {
        $('.alert').removeClass('alert-success');
    }
};